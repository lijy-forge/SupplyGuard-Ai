package ai.factoryops.business.api;

import ai.factoryops.business.service.FactoryOpsService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import java.util.*;

@RestController @RequestMapping("/api/v1")
public class FactoryOpsController {
  private final FactoryOpsService service; public FactoryOpsController(FactoryOpsService service){this.service=service;}
  public record ActionRequest(@NotBlank String actionType,@NotBlank String description,@NotBlank String actor,String correlationId){}
  @GetMapping("/health") public Map<String,String> health(){return Map.of("status","UP","service","business-service");}
  @GetMapping("/suppliers/{code}") public Object supplier(@PathVariable String code){return service.supplier(code);}
  @GetMapping("/suppliers/{code}/parts") public Object supplierParts(@PathVariable String code){return service.supplierParts(code);}
  @GetMapping("/parts/{number}") public Object part(@PathVariable String number){return service.part(number);}
  @GetMapping("/parts/{number}/impact") public Object impact(@PathVariable String number){return service.impact(number);}
  @GetMapping("/batches/{number}") public Object batch(@PathVariable String number){return service.batch(number);}
  @GetMapping("/batches/{number}/context") public Object context(@PathVariable String number){return service.batchContext(number);}
  @GetMapping("/quality-cases/{number}") public Object qualityCase(@PathVariable String number){return service.qualityCase(number);}
  @GetMapping("/quality-cases/{number}/actions") public Object actions(@PathVariable String number){return service.actions(number);}
  @GetMapping("/quality-cases/{number}/audit") public Object audit(@PathVariable String number){return service.audit(number);}
  @PostMapping("/quality-cases/{number}/actions") public ResponseEntity<Object> action(@PathVariable String number,@Valid @RequestBody ActionRequest r){
    var cid=r.correlationId()==null||r.correlationId().isBlank()?UUID.randomUUID().toString():r.correlationId();
    return ResponseEntity.status(201).body(service.createAction(number,r.actionType(),r.description(),r.actor(),cid));
  }
  @ExceptionHandler(NoSuchElementException.class) ResponseEntity<Object> notFound(){return ResponseEntity.status(404).body(Map.of("error","not_found"));}
}
