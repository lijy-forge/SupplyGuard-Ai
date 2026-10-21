package ai.factoryops.business;

import ai.factoryops.business.repository.Repositories.*;
import ai.factoryops.business.service.FactoryOpsService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
class FactoryOpsIntegrationTest {
  @Autowired FactoryOpsService service; @Autowired OutboxRepository outbox; @Autowired AuditRepository audits;
  @MockitoBean RabbitTemplate rabbit;
  @Test void goldenPathReadsImpactAndPersistsApprovedActionAtomically(){
    assertThat(service.supplier("SUP-001").riskLevel).isEqualTo("HIGH");
    assertThat(service.impact("PART-001")).hasSize(2);
    assertThat(service.batchContext("BATCH-001").get("issues")).asList().hasSize(1);
    var action=service.createAction("CASE-001","SUPPLIER_CONTAINMENT","Issue 8D and quarantine stock","quality.lead","corr-test-1");
    assertThat(action.id).isNotBlank(); assertThat(audits.findByEntityIdOrderByCreatedAtDesc("case-001")).hasSize(1);
    assertThat(outbox.findTop50ByPublishedAtIsNullOrderByCreatedAtAsc()).hasSize(1);
  }
}
