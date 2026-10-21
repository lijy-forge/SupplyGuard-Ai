package ai.factoryops.business;
import ai.factoryops.business.api.SupplierRiskController;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.web.server.ResponseStatusException;
import static org.assertj.core.api.Assertions.*;
@SpringBootTest
class SupplierRiskIntegrationTest {
 @Autowired SupplierRiskController controller;
 @MockitoBean RabbitTemplate rabbit;
 @Test void migrationSeedsFourCandidatesAndQualification() {
   var rows=controller.candidates("PART-001");
   assertThat(rows).hasSize(4);
   assertThat(rows.get(1).supplierCode()).isEqualTo("SUP-002");
   assertThat(rows.get(1).capacityUnits()).isEqualTo(8000);
   assertThat(rows.get(3).qualified()).isFalse();
 }
 @Test void unknownPartAndInvalidInput() {
   assertThatThrownBy(()->controller.candidates("UNKNOWN")).isInstanceOf(ResponseStatusException.class).hasMessageContaining("404");
   assertThatThrownBy(()->controller.candidates(" ")).isInstanceOf(ResponseStatusException.class).hasMessageContaining("400");
   assertThatThrownBy(()->controller.candidates("' OR 1=1 --")).isInstanceOf(ResponseStatusException.class).hasMessageContaining("404");
 }
}
