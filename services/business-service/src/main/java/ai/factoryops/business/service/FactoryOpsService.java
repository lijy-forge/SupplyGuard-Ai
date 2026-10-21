package ai.factoryops.business.service;

import ai.factoryops.business.domain.DomainEntities.*;
import ai.factoryops.business.repository.Repositories.*;
import jakarta.transaction.Transactional;
import org.springframework.stereotype.Service;
import java.time.Instant;
import java.util.*;

@Service
public class FactoryOpsService {
  private final SupplierRepository suppliers; private final PartRepository parts; private final SupplierPartRepository supplierParts;
  private final BomRepository boms; private final BatchRepository batches; private final InspectionRepository inspections;
  private final IssueBatchRepository issueBatches; private final CaseRepository cases; private final CaseIssueRepository caseIssues;
  private final ActionRepository actions; private final AuditRepository audits; private final OutboxRepository outbox;
  public FactoryOpsService(SupplierRepository a, PartRepository b, SupplierPartRepository c, BomRepository d, BatchRepository e,
      InspectionRepository f, IssueBatchRepository g, CaseRepository h, CaseIssueRepository i, ActionRepository j, AuditRepository k, OutboxRepository l){
    suppliers=a;parts=b;supplierParts=c;boms=d;batches=e;inspections=f;issueBatches=g;cases=h;caseIssues=i;actions=j;audits=k;outbox=l;
  }
  public Supplier supplier(String code){ return suppliers.findBySupplierCode(code).orElseThrow(); }
  public Part part(String number){ return parts.findByPartNumber(number).orElseThrow(); }
  public List<SupplierPart> supplierParts(String code){ return supplierParts.findBySupplier_Id(supplier(code).id); }
  public List<BomItem> impact(String number){ return boms.findByPart_Id(part(number).id); }
  public Batch batch(String number){ return batches.findByBatchNumber(number).orElseThrow(); }
  public Map<String,Object> batchContext(String number){ var b=batch(number); return Map.of("batch",b,"inspections",inspections.findByBatch_Id(b.id),"issues",issueBatches.findByBatch_Id(b.id)); }
  public QualityCase qualityCase(String number){ return cases.findByCaseNumber(number).orElseThrow(); }
  public List<CorrectiveAction> actions(String number){ return actions.findByQualityCase_IdOrderByCreatedAtDesc(qualityCase(number).id); }
  public List<AuditEvent> audit(String number){ return audits.findByEntityIdOrderByCreatedAtDesc(qualityCase(number).id); }
  @Transactional public CorrectiveAction createAction(String caseNumber,String type,String description,String actor,String correlationId){
    var qc=qualityCase(caseNumber); var action=new CorrectiveAction(); action.qualityCase=qc; action.actionType=type; action.description=description;
    action.actionNumber="CA-"+UUID.randomUUID().toString().substring(0,8).toUpperCase(); action.title=type+" for "+caseNumber;
    action.status="OPEN"; action.assignee=actor; action.dueDate=java.time.LocalDate.now().plusDays(14); action.correlationId=correlationId; actions.save(action);
    var audit=new AuditEvent(); audit.actorType="USER"; audit.entityType="QUALITY_CASE"; audit.entityId=qc.id; audit.action="CORRECTIVE_ACTION_CREATED";
    audit.actor=actor; audit.correlationId=correlationId; audit.arguments="{\"caseNumber\":\""+caseNumber+"\"}"; audit.result="{\"actionId\":\""+action.id+"\"}"; audits.save(audit);
    var event=new OutboxEvent(); event.aggregateType="QUALITY_CASE"; event.aggregateId=qc.id; event.eventType="corrective-action.created";
    event.correlationId=correlationId; event.payload="{\"caseNumber\":\""+caseNumber+"\",\"actionId\":\""+action.id+"\",\"correlationId\":\""+correlationId+"\"}"; outbox.save(event);
    return action;
  }
}
