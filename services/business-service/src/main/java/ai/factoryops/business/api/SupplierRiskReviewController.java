package ai.factoryops.business.api;
import ai.factoryops.business.service.SupplierRiskReviewService;
import com.fasterxml.jackson.databind.JsonNode;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import org.springframework.web.bind.annotation.*;
import java.util.*;
@RestController
@RequestMapping("/api/v1/supplier-risk/reviews")
public class SupplierRiskReviewController {
 private final SupplierRiskReviewService service;
 public SupplierRiskReviewController(SupplierRiskReviewService service){this.service=service;}
 public record Create(@NotBlank @Size(max=80) String request_key,@NotBlank @Size(max=80) String case_number,@NotNull JsonNode snapshot){}
 public record Decision(@Min(0) long version,boolean approved,@NotNull @Size(max=50) String supplier_code,@NotBlank @Size(max=100) String actor,@NotBlank @Size(max=2000) String reason){}
 @PostMapping public Object create(@Valid @RequestBody Create r){return service.create(r.request_key(),r.case_number(),r.snapshot());}
 @GetMapping("/{id}") public Object get(@PathVariable String id){return service.get(id);}
 @PostMapping("/{id}/decision") public Object decide(@PathVariable String id,@Valid @RequestBody Decision r){return service.decide(id,r.version(),r.approved(),r.supplier_code(),r.actor(),r.reason());}
 @GetMapping("/{id}/audit") public Object audit(@PathVariable String id){return service.audit(id);}
 @ExceptionHandler(org.springframework.dao.DuplicateKeyException.class)
 @ResponseStatus(org.springframework.http.HttpStatus.CONFLICT)
 public Object duplicateKey(){return Map.of("error","request_key_conflict");}
}
