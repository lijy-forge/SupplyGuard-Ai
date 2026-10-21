package ai.factoryops.business;

import ai.factoryops.business.api.SupplierRiskController;
import ai.factoryops.business.service.SupplierRiskReviewService;
import com.fasterxml.jackson.databind.*;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.transaction.annotation.*;
import java.util.*;
import java.util.concurrent.*;
import java.sql.Timestamp;
import java.time.*;
import static org.assertj.core.api.Assertions.*;

@SpringBootTest
@Transactional
class SupplierRiskReviewIntegrationTest {
 @Autowired SupplierRiskReviewService service;
 @Autowired SupplierRiskController candidates;
 @Autowired ObjectMapper mapper;
 @Autowired jakarta.persistence.EntityManager entityManager;
 @Autowired JdbcTemplate jdbc;
 @MockitoBean RabbitTemplate rabbit;
 JsonNode snapshot(boolean complete){
   var candidate=mapper.valueToTree(candidates.candidates("PART-001").get(1));
   ((com.fasterxml.jackson.databind.node.ObjectNode)candidate).putArray("exclusions");
   return mapper.valueToTree(Map.of("part_number","PART-001","request",Map.of("part_number","PART-001","case_number","CASE-001","current_supplier","SUP-001","required_units",4000,"max_lead_days",21),"analysis_status",complete?"READY_FOR_REVIEW":"NEEDS_EVIDENCE","recommendations",List.of(candidate),"evidence",List.of(
     Map.of("source_type","STRUCTURED","status","AVAILABLE","payload",Map.of("cases",List.of(Map.of("supplierCode","SUP-001")))),
     Map.of("source_type","GRAPH","status","AVAILABLE","payload",Map.of("vehicles",List.of(Map.of("model","VM-A")))),
     Map.of("source_type","DOCUMENT","status",complete?"AVAILABLE":"DEMO","payload",Map.of("matches",List.of(Map.of("id","TEST-SOP")))))));
 }
 Map<String,Object> create(boolean complete){return service.create(UUID.randomUUID().toString(),"CASE-001",snapshot(complete));}
 @Test void contextAssociatesRealCasePartSupplierAndTwoVehicles(){
   var ctx=candidates.context("PART-001","CASE-001");
   assertThat((List<?>)ctx.get("vehicles")).hasSize(2);
   assertThat(ctx.get("cases").toString()).contains("SUP-001").contains("ISSUE-001");
   assertThatThrownBy(()->candidates.context("PART-001","UNKNOWN")).hasMessageContaining("404");
 }
 @Test void sameKeySameSnapshotReturnsSameReviewAndDifferentSnapshotConflicts(){
   String key=UUID.randomUUID().toString();var snapshot=snapshot(true);
   var a=service.create(key,"CASE-001",snapshot);var b=service.create(key,"CASE-001",snapshot);
   assertThat(b.get("id")).isEqualTo(a.get("id"));
   assertThat(service.audit(a.get("id").toString())).hasSize(1);
   assertThatThrownBy(()->service.create(key,"CASE-001",snapshot(false))).hasMessageContaining("409");
 }
 @Test void approvalCreatesExactlyOneActionOutboxAndReviewAudit(){
   var review=create(true);String id=review.get("id").toString();
   var first=service.decide(id,0,true,"SUP-002","test.reviewer","reviewed evidence");
   var repeat=service.decide(id,0,true,"SUP-002","test.reviewer","reviewed evidence");
   entityManager.flush(); // JDBC assertions must see JPA writes inside this rollback-only test transaction.
   assertThat(first.get("status")).isEqualTo("APPROVED");assertThat(repeat.get("action_id")).isEqualTo(first.get("action_id"));
   assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM corrective_actions WHERE correlation_id=?",Integer.class,"risk-review-"+id)).isEqualTo(1);
   assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM outbox_events WHERE correlation_id=?",Integer.class,"risk-review-"+id)).isEqualTo(1);
   assertThat(service.audit(id)).hasSize(2);
   assertThatThrownBy(()->service.decide(id,1,false,"SUP-002","test.reviewer","changed decision")).hasMessageContaining("409");
 }
 @Test void rejectionHasNoActionOrOutboxAndIsIdempotent(){
   String id=create(true).get("id").toString();
   service.decide(id,0,false,"SUP-002","test.reviewer","reject");
   assertThat(service.decide(id,0,false,"SUP-002","test.reviewer","reject").get("status")).isEqualTo("REJECTED");
   assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM outbox_events WHERE correlation_id=?",Integer.class,"risk-review-"+id)).isZero();
 }
 @Test void incompleteEvidenceAndStaleVersionCannotApprove(){
   String blocked=create(false).get("id").toString();
   assertThatThrownBy(()->service.decide(blocked,0,true,"SUP-002","test","reason")).hasMessageContaining("409");
   String fresh=create(true).get("id").toString();
   assertThatThrownBy(()->service.decide(fresh,9,true,"SUP-002","test","reason")).hasMessageContaining("409");
   assertThat(service.get(fresh).get("status")).isEqualTo("PENDING_REVIEW");
 }
 @Test void unlistedSupplierExpiredAssessmentAndChangedMetricsCannotApprove(){
   String id=create(true).get("id").toString();
   assertThatThrownBy(()->service.decide(id,0,true,"SUP-004","test","reason")).hasMessageContaining("409");
   jdbc.update("UPDATE supplier_risk_reviews SET created_at=? WHERE id=?",Timestamp.from(Instant.now().minus(Duration.ofHours(25))),id);
   assertThatThrownBy(()->service.decide(id,0,true,"SUP-002","test","reason")).hasMessageContaining("409");
   String fresh=create(true).get("id").toString();
   jdbc.update("UPDATE supplier_risk_metrics SET capacity_units=1 WHERE supplier_id='sup-002'");
   assertThatThrownBy(()->service.decide(fresh,0,true,"SUP-002","test","reason")).hasMessageContaining("409");
 }
 @Test void snapshotMustMatchCaseAndSupplier(){
   var data=(com.fasterxml.jackson.databind.node.ObjectNode)snapshot(true);
   ((com.fasterxml.jackson.databind.node.ObjectNode)data.get("request")).put("current_supplier","SUP-002");
   assertThatThrownBy(()->service.create(UUID.randomUUID().toString(),"CASE-001",data)).hasMessageContaining("400");
 }
 @Test @Transactional(propagation=Propagation.NOT_SUPPORTED)
 void concurrentIdenticalApprovalsCreateOneAction() throws Exception {
   String id=create(true).get("id").toString();var start=new CountDownLatch(1);
   try(var pool=Executors.newFixedThreadPool(2)){
     Callable<Map<String,Object>> task=()->{start.await();return service.decide(id,0,true,"SUP-002","test.concurrent","same reason");};
     var first=pool.submit(task);var second=pool.submit(task);start.countDown();
     assertThat(first.get(20,TimeUnit.SECONDS).get("action_id")).isEqualTo(second.get(20,TimeUnit.SECONDS).get("action_id"));
     assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM corrective_actions WHERE correlation_id=?",Integer.class,"risk-review-"+id)).isEqualTo(1);
   } finally {
     jdbc.update("DELETE FROM supplier_risk_reviews WHERE id=?",id);
     jdbc.update("DELETE FROM outbox_events WHERE correlation_id=?","risk-review-"+id);
     jdbc.update("DELETE FROM audit_events WHERE correlation_id=?","risk-review-"+id);
     jdbc.update("DELETE FROM corrective_actions WHERE correlation_id=?","risk-review-"+id);
   }
 }
}
