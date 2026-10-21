package ai.factoryops.business.repository;

import ai.factoryops.business.domain.DomainEntities.*;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.*;

public final class Repositories {
  private Repositories() {}
  public interface SupplierRepository extends JpaRepository<Supplier,String>{ Optional<Supplier> findBySupplierCode(String code); }
  public interface PartRepository extends JpaRepository<Part,String>{ Optional<Part> findByPartNumber(String number); }
  public interface SupplierPartRepository extends JpaRepository<SupplierPart,String>{ List<SupplierPart> findBySupplier_Id(String id); }
  public interface BomRepository extends JpaRepository<BomItem,String>{ List<BomItem> findByPart_Id(String id); }
  public interface BatchRepository extends JpaRepository<Batch,String>{ Optional<Batch> findByBatchNumber(String number); }
  public interface InspectionRepository extends JpaRepository<InspectionRecord,String>{ List<InspectionRecord> findByBatch_Id(String id); }
  public interface IssueBatchRepository extends JpaRepository<QualityIssueBatch,String>{ List<QualityIssueBatch> findByBatch_Id(String id); }
  public interface CaseRepository extends JpaRepository<QualityCase,String>{ Optional<QualityCase> findByCaseNumber(String number); }
  public interface CaseIssueRepository extends JpaRepository<QualityCaseIssue,String>{ List<QualityCaseIssue> findByQualityCase_Id(String id); }
  public interface ActionRepository extends JpaRepository<CorrectiveAction,String>{ List<CorrectiveAction> findByQualityCase_IdOrderByCreatedAtDesc(String id); }
  public interface AuditRepository extends JpaRepository<AuditEvent,String>{ List<AuditEvent> findByEntityIdOrderByCreatedAtDesc(String id); }
  public interface OutboxRepository extends JpaRepository<OutboxEvent,String>{ List<OutboxEvent> findTop50ByPublishedAtIsNullOrderByCreatedAtAsc(); }
}
