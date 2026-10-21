package ai.factoryops.business.domain;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.*;

public final class DomainEntities {
    private DomainEntities() {}

    @MappedSuperclass
    public abstract static class BaseEntity {
        @Id @Column(length=36) public String id;
        @Version @Column(name="record_version", nullable=false) public long recordVersion;
        @Column(name="created_at", nullable=false) public Instant createdAt;
        @Column(name="updated_at", nullable=false) public Instant updatedAt;
        @PrePersist void create() { var now=Instant.now(); if(id==null) id=java.util.UUID.randomUUID().toString(); if(createdAt==null) createdAt=now; updatedAt=now; }
        @PreUpdate void update() { updatedAt=Instant.now(); }
    }

    @Entity @Table(name="suppliers") public static class Supplier extends BaseEntity {
        @Column(name="supplier_code", unique=true, nullable=false, length=50) public String supplierCode;
        @Column(nullable=false) public String name;
        @Column(nullable=false) public String category;
        @Column(nullable=false) public String country;
        @Column(nullable=false) public String status;
        @Column(name="risk_level", nullable=false) public String riskLevel;
    }
    @Entity @Table(name="parts") public static class Part extends BaseEntity {
        @Column(name="part_number", unique=true, nullable=false, length=80) public String partNumber;
        @Column(nullable=false) public String name;
        @Column(nullable=false) public String category;
        @Column(nullable=false, columnDefinition="TEXT") public String specification;
        @Column(nullable=false) public String status;
    }
    @Entity @Table(name="vehicle_models") public static class VehicleModel extends BaseEntity {
        @Column(name="model_code", unique=true, nullable=false, length=50) public String modelCode;
        @Column(nullable=false) public String name;
        @Column(nullable=false) public String platform;
        @Column(nullable=false) public String status;
    }
    @Entity @Table(name="supplier_parts", uniqueConstraints=@UniqueConstraint(columnNames={"supplier_id","part_id"})) public static class SupplierPart extends BaseEntity {
        @JsonIgnore @ManyToOne(fetch=FetchType.LAZY) @JoinColumn(name="supplier_id", nullable=false) public Supplier supplier;
        @JsonIgnore @ManyToOne(fetch=FetchType.LAZY) @JoinColumn(name="part_id", nullable=false) public Part part;
        @Column(name="supplier_part_number", nullable=false) public String supplierPartNumber;
        @Column(name="lead_time_days", nullable=false) public int leadTimeDays;
        @Column(nullable=false) public String status;
    }
    @Entity @Table(name="bom_items", uniqueConstraints=@UniqueConstraint(columnNames={"vehicle_model_id","part_id","bom_version","effective_from"})) public static class BomItem extends BaseEntity {
        @JsonIgnore @ManyToOne(fetch=FetchType.LAZY) @JoinColumn(name="vehicle_model_id", nullable=false) public VehicleModel vehicleModel;
        @JsonIgnore @ManyToOne(fetch=FetchType.LAZY) @JoinColumn(name="part_id", nullable=false) public Part part;
        @Column(nullable=false, precision=12, scale=3) public BigDecimal quantity;
        @Column(name="bom_version", nullable=false) public String bomVersion;
        @Column(name="effective_from", nullable=false) public LocalDate effectiveFrom;
        @Column(name="effective_to") public LocalDate effectiveTo;
    }
    @Entity @Table(name="batches") public static class Batch extends BaseEntity {
        @Column(name="batch_number", unique=true, nullable=false, length=80) public String batchNumber;
        @JsonIgnore @ManyToOne(fetch=FetchType.LAZY) @JoinColumn(name="part_id", nullable=false) public Part part;
        @JsonIgnore @ManyToOne(fetch=FetchType.LAZY) @JoinColumn(name="supplier_id", nullable=false) public Supplier supplier;
        @Column(name="manufactured_at", nullable=false) public Instant manufacturedAt;
        @Column(name="received_at") public Instant receivedAt;
        @Column(nullable=false) public int quantity;
        @Column(nullable=false) public String status;
    }
    @Entity @Table(name="inspection_records") public static class InspectionRecord extends BaseEntity {
        @Column(name="inspection_number", unique=true, nullable=false) public String inspectionNumber;
        @JsonIgnore @ManyToOne(fetch=FetchType.LAZY) @JoinColumn(name="batch_id", nullable=false) public Batch batch;
        @Column(name="inspection_type", nullable=false) public String inspectionType;
        @Column(name="metric_name", nullable=false) public String metricName;
        @Column(name="measured_value", nullable=false, precision=18, scale=6) public BigDecimal measuredValue;
        @Column(name="lower_limit", nullable=false, precision=18, scale=6) public BigDecimal lowerLimit;
        @Column(name="upper_limit", nullable=false, precision=18, scale=6) public BigDecimal upperLimit;
        @Column(nullable=false) public String result;
        @Column(name="inspected_at", nullable=false) public Instant inspectedAt;
    }
    @Entity @Table(name="quality_issues") public static class QualityIssue extends BaseEntity {
        @Column(name="issue_number", unique=true, nullable=false) public String issueNumber;
        @Column(nullable=false) public String title;
        @Column(nullable=false, columnDefinition="TEXT") public String description;
        @Column(nullable=false) public String severity;
        @Column(nullable=false) public String status;
        @Column(name="detected_at", nullable=false) public Instant detectedAt;
        @Column(nullable=false) public String source;
    }
    @Entity @Table(name="quality_issue_batches", uniqueConstraints=@UniqueConstraint(columnNames={"quality_issue_id","batch_id"})) public static class QualityIssueBatch extends BaseEntity {
        @JsonIgnore @ManyToOne(fetch=FetchType.LAZY) @JoinColumn(name="quality_issue_id", nullable=false) public QualityIssue issue;
        @JsonIgnore @ManyToOne(fetch=FetchType.LAZY) @JoinColumn(name="batch_id", nullable=false) public Batch batch;
    }
    @Entity @Table(name="quality_cases") public static class QualityCase extends BaseEntity {
        @Column(name="case_number", unique=true, nullable=false) public String caseNumber;
        @Column(nullable=false) public String title;
        @Column(nullable=false, columnDefinition="TEXT") public String description;
        @Column(nullable=false) public String priority;
        @Column(nullable=false) public String status;
        @Column(nullable=false) public String owner;
        @Column(name="opened_at", nullable=false) public Instant openedAt;
        @Column(name="closed_at") public Instant closedAt;
    }
    @Entity @Table(name="quality_case_issues", uniqueConstraints=@UniqueConstraint(columnNames={"quality_case_id","quality_issue_id"})) public static class QualityCaseIssue extends BaseEntity {
        @JsonIgnore @ManyToOne(fetch=FetchType.LAZY) @JoinColumn(name="quality_case_id", nullable=false) public QualityCase qualityCase;
        @JsonIgnore @ManyToOne(fetch=FetchType.LAZY) @JoinColumn(name="quality_issue_id", nullable=false) public QualityIssue issue;
    }
    @Entity @Table(name="corrective_actions") public static class CorrectiveAction extends BaseEntity {
        @Column(name="action_number", unique=true, nullable=false) public String actionNumber;
        @JsonIgnore @ManyToOne(fetch=FetchType.LAZY) @JoinColumn(name="quality_case_id", nullable=false) public QualityCase qualityCase;
        @Column(nullable=false) public String title;
        @Column(nullable=false, columnDefinition="TEXT") public String description;
        @Column(name="action_type", nullable=false) public String actionType;
        @Column(nullable=false) public String status;
        @Column(nullable=false) public String assignee;
        @Column(name="due_date", nullable=false) public LocalDate dueDate;
        @Column(name="correlation_id", nullable=false) public String correlationId;
    }
    @Entity @Table(name="documents", uniqueConstraints=@UniqueConstraint(columnNames={"document_number","version"})) public static class DocumentMetadata extends BaseEntity {
        @Column(name="document_number", nullable=false) public String documentNumber;
        @Column(nullable=false) public String title;
        @Column(name="document_type", nullable=false) public String documentType;
        @Column(nullable=false) public String version;
        @Column(name="source_uri", nullable=false) public String sourceUri;
        @Column(nullable=false) public String status;
    }
    @Entity @Table(name="audit_events") public static class AuditEvent extends BaseEntity {
        @Column(name="actor_type", nullable=false) public String actorType;
        @Column(nullable=false) public String actor;
        @Column(nullable=false) public String action;
        @Column(name="entity_type", nullable=false) public String entityType;
        @Column(name="entity_id", nullable=false) public String entityId;
        @Column(nullable=false, columnDefinition="TEXT") public String arguments;
        @Column(nullable=false, columnDefinition="TEXT") public String result;
        @Column(name="correlation_id", nullable=false) public String correlationId;
    }
    @Entity @Table(name="outbox_events") public static class OutboxEvent extends BaseEntity {
        @Column(name="event_type", nullable=false) public String eventType;
        @Column(name="aggregate_type", nullable=false) public String aggregateType;
        @Column(name="aggregate_id", nullable=false) public String aggregateId;
        @Column(nullable=false, columnDefinition="TEXT") public String payload;
        @Column(name="correlation_id", nullable=false) public String correlationId;
        @Column(name="published_at") public Instant publishedAt;
    }
}
