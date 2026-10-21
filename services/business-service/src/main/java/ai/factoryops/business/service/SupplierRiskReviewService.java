package ai.factoryops.business.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.HttpStatus;
import ai.factoryops.business.api.SupplierRiskController;
import java.time.*;
import java.sql.Timestamp;
import java.util.*;

@Service
public class SupplierRiskReviewService {
  private final JdbcTemplate jdbc;
  private final ObjectMapper mapper;
  private final FactoryOpsService business;
  private final SupplierRiskController candidates;
  public SupplierRiskReviewService(JdbcTemplate jdbc,ObjectMapper mapper,FactoryOpsService business,SupplierRiskController candidates) {
    this.jdbc=jdbc;this.mapper=mapper;this.business=business;this.candidates=candidates;
  }
  private ResponseStatusException error(HttpStatus status,String msg){return new ResponseStatusException(status,msg);}
  private String json(Object value){try{return mapper.writeValueAsString(value);}catch(Exception e){throw error(HttpStatus.BAD_REQUEST,"invalid JSON");}}
  private JsonNode parse(String value){try{return mapper.readTree(value);}catch(Exception e){throw new IllegalStateException("invalid stored snapshot",e);}}
  public Map<String,Object> get(String id){
    var rows=jdbc.queryForList("SELECT * FROM supplier_risk_reviews WHERE id=?",id);
    if(rows.isEmpty())throw error(HttpStatus.NOT_FOUND,"review not found");
    var row=rows.getFirst();
    var result=new LinkedHashMap<String,Object>();
    result.put("id",row.get("id"));result.put("status",row.get("status"));result.put("version",row.get("record_version"));
    result.put("created_at",row.get("created_at").toString());result.put("snapshot",parse(row.get("snapshot").toString()));
    result.put("decision",row.get("decision")==null?null:parse(row.get("decision").toString()));
    result.put("action_id",row.get("action_id"));return result;
  }
  private boolean complete(JsonNode snapshot){
    for(String type:List.of("STRUCTURED","GRAPH","DOCUMENT")) {
      boolean found=false;
      for(JsonNode e:snapshot.path("evidence")) {
        String field=type.equals("STRUCTURED")?"cases":type.equals("GRAPH")?"vehicles":"matches";
        var payload=e.path("payload").path(field);
        if(type.equals(e.path("source_type").asText())&&"AVAILABLE".equals(e.path("status").asText())&&payload.isArray()&&!payload.isEmpty())found=true;
      }
      if(!found)return false;
    }
    return "READY_FOR_REVIEW".equals(snapshot.path("analysis_status").asText());
  }
  @Transactional
  public Map<String,Object> create(String key,String caseNumber,JsonNode snapshot){
    if(!snapshot.isObject()||snapshot.toString().length()>200000)throw error(HttpStatus.BAD_REQUEST,"invalid snapshot");
    var existing=jdbc.queryForList("SELECT id,case_number,snapshot FROM supplier_risk_reviews WHERE request_key=?",key);
    if(!existing.isEmpty()) {
      var row=existing.getFirst();
      if(!caseNumber.equals(row.get("case_number"))||!snapshot.equals(parse(row.get("snapshot").toString())))throw error(HttpStatus.CONFLICT,"request key reused with different input");
      return get(row.get("id").toString());
    }
    String part=snapshot.path("part_number").asText();
    String current=snapshot.path("request").path("current_supplier").asText();
    if(!caseNumber.equals(snapshot.path("request").path("case_number").asText())||!part.equals(snapshot.path("request").path("part_number").asText()))throw error(HttpStatus.BAD_REQUEST,"snapshot context mismatch");
    var context=candidates.context(part,caseNumber);
    @SuppressWarnings("unchecked") var links=(List<Map<String,Object>>)context.get("cases");
    if(links.stream().noneMatch(c->current.equals(c.get("supplierCode"))))throw error(HttpStatus.BAD_REQUEST,"case is not linked to current supplier");
    if(snapshot.path("request").path("required_units").asInt()<=0||snapshot.path("request").path("max_lead_days").asInt()<=0)throw error(HttpStatus.BAD_REQUEST,"invalid constraints");
    String id=UUID.randomUUID().toString();String status=complete(snapshot)&&snapshot.path("recommendations").isArray()&&!snapshot.path("recommendations").isEmpty()?"PENDING_REVIEW":"NEEDS_EVIDENCE";
    jdbc.update("INSERT INTO supplier_risk_reviews(id,request_key,case_number,part_number,current_supplier,snapshot,status,record_version,created_at) VALUES(?,?,?,?,?,?,?,0,?)",id,key,caseNumber,part,current,json(snapshot),status,Timestamp.from(Instant.now()));
    audit(id,"RISK_REVIEW_CREATED","agent",Map.of("status",status));return get(id);
  }
  @Transactional
  public Map<String,Object> decide(String id,long version,boolean approve,String supplier,String actor,String reason){
    // Row lock serializes approvals and retries across service instances.
    var rows=jdbc.queryForList("SELECT * FROM supplier_risk_reviews WHERE id=? FOR UPDATE",id);
    if(rows.isEmpty())throw error(HttpStatus.NOT_FOUND,"review not found");
    var row=rows.getFirst();var decision=Map.of("approved",approve,"supplier_code",supplier,"actor",actor,"reason",reason);
    if(row.get("decision")!=null) {
      if(parse(row.get("decision").toString()).equals(mapper.valueToTree(decision)))return get(id);
      throw error(HttpStatus.CONFLICT,"review already decided");
    }
    if(((Number)row.get("record_version")).longValue()!=version)throw error(HttpStatus.CONFLICT,"stale review version");
    String actionId=null;
    if(approve){
      if(!"PENDING_REVIEW".equals(row.get("status")))throw error(HttpStatus.CONFLICT,"evidence incomplete; approval blocked");
      if(((Timestamp)row.get("created_at")).toInstant().isBefore(Instant.now().minus(Duration.ofHours(24))))throw error(HttpStatus.CONFLICT,"assessment expired; reassess");
      var snapshot=parse(row.get("snapshot").toString());boolean recommended=false;
      for(var r:snapshot.path("recommendations"))if(supplier.equals(r.path("supplierCode").asText())&&r.path("exclusions").isArray()&&r.path("exclusions").isEmpty())recommended=true;
      if(!recommended||supplier.equals(row.get("current_supplier")))throw error(HttpStatus.CONFLICT,"supplier not recommended");
      var currentContext=candidates.context(row.get("part_number").toString(),row.get("case_number").toString());
      @SuppressWarnings("unchecked") var linkedCases=(List<Map<String,Object>>)currentContext.get("cases");
      if(linkedCases.stream().anyMatch(x->"CLOSED".equals(x.get("status"))))throw error(HttpStatus.CONFLICT,"quality case closed; reassess");
      var c=candidates.candidates(row.get("part_number").toString()).stream().filter(x->supplier.equals(x.supplierCode())).findFirst().orElseThrow(()->error(HttpStatus.CONFLICT,"supplier inactive"));
      var req=snapshot.path("request");
      if(c.defectPpm()==null||c.onTimeRate()==null||!Boolean.TRUE.equals(c.qualified())||c.capacityUnits()==null||c.capacityUnits()<req.path("required_units").asInt()||c.leadTimeDays()>req.path("max_lead_days").asInt())throw error(HttpStatus.CONFLICT,"supplier no longer meets constraints");
      if(c.observedAt()==null||c.observedAt().isBefore(Instant.now().minus(Duration.ofDays(30)))||c.observedAt().isAfter(Instant.now().plusSeconds(300)))throw error(HttpStatus.CONFLICT,"metrics stale; reassess");
      JsonNode previous=null;
      for(var r:snapshot.path("recommendations"))if(supplier.equals(r.path("supplierCode").asText()))previous=r;
      if(previous==null||previous.path("capacityUnits").asInt()!=c.capacityUnits()||previous.path("leadTimeDays").asInt()!=c.leadTimeDays()||previous.path("defectPpm").asInt()!=c.defectPpm()||Double.compare(previous.path("onTimeRate").asDouble(),c.onTimeRate())!=0)throw error(HttpStatus.CONFLICT,"metrics changed; reassess");
      String description="Review supplier switch for "+row.get("part_number")+" from "+row.get("current_supplier")+" to "+supplier+". Risk review "+id+". Rationale: "+reason+". Complete qualification and procurement review before any sourcing change.";
      actionId=business.createAction(row.get("case_number").toString(),"SUPPLIER_SWITCH_REVIEW",description,actor,"risk-review-"+id).id;
    }
    jdbc.update("UPDATE supplier_risk_reviews SET status=?,record_version=record_version+1,reviewed_at=?,decision=?,action_id=? WHERE id=?",approve?"APPROVED":"REJECTED",Timestamp.from(Instant.now()),json(decision),actionId,id);
    audit(id,approve?"RISK_REVIEW_APPROVED":"RISK_REVIEW_REJECTED",actor,decision);
    return get(id);
  }
  private void audit(String id,String action,String actor,Object payload){
    var now=Timestamp.from(Instant.now());
    jdbc.update("INSERT INTO audit_events(id,record_version,created_at,updated_at,actor_type,actor,action,entity_type,entity_id,arguments,result,correlation_id) VALUES(?,0,?,?,?, ?,?,?,?, ?,?,?)",UUID.randomUUID().toString(),now,now,"USER",actor,action,"SUPPLIER_RISK_REVIEW",id,"{}",json(payload),"risk-review-"+id);
  }
  public List<Map<String,Object>> audit(String id){get(id);return jdbc.queryForList("SELECT action,actor,result,created_at FROM audit_events WHERE entity_id=? ORDER BY created_at,id",id);}
}
