package ai.factoryops.business.api;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.HttpStatus;
import java.util.*;

@RestController
@RequestMapping("/api/v1/supplier-risk")
public class SupplierRiskController {
  private final JdbcTemplate jdbc;
  public SupplierRiskController(JdbcTemplate jdbc) { this.jdbc=jdbc; }
  public record Candidate(String supplierCode,String name,int leadTimeDays,Double onTimeRate,Integer defectPpm,Integer capacityUnits,Boolean qualified,java.time.Instant observedAt) {}
  @GetMapping("/candidates")
  public List<Candidate> candidates(@RequestParam String partNumber) {
    if (partNumber.isBlank() || partNumber.length()>80) throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"invalid partNumber");
    if (jdbc.queryForObject("SELECT COUNT(*) FROM parts WHERE part_number=?",Integer.class,partNumber)==0)
      throw new ResponseStatusException(HttpStatus.NOT_FOUND,"part not found");
    return jdbc.query("""
      SELECT s.supplier_code,s.name,sp.lead_time_days,m.on_time_rate,m.defect_ppm,m.capacity_units,m.qualified,m.observed_at
      FROM supplier_parts sp JOIN suppliers s ON s.id=sp.supplier_id JOIN parts p ON p.id=sp.part_id
      LEFT JOIN supplier_risk_metrics m ON m.supplier_id=s.id
      WHERE p.part_number=? AND p.status='ACTIVE' AND s.status='ACTIVE' AND sp.status='ACTIVE'
      ORDER BY s.supplier_code
      """,(rs,n)-> new Candidate(rs.getString(1),rs.getString(2),rs.getInt(3),rs.getObject(4,Double.class),rs.getObject(5,Integer.class),rs.getObject(6,Integer.class),rs.getObject(7,Boolean.class),rs.getTimestamp(8)==null?null:rs.getTimestamp(8).toInstant()),partNumber);
  }
  @GetMapping("/context")
  public Map<String,Object> context(@RequestParam String partNumber, @RequestParam String caseNumber) {
    candidates(partNumber);
    var cases=jdbc.queryForList("""
      SELECT DISTINCT qc.case_number AS caseNumber,qc.status AS status,qi.issue_number AS issueNumber,
        qi.severity AS severity,b.batch_number AS batchNumber,s.supplier_code AS supplierCode
      FROM quality_cases qc JOIN quality_case_issues qci ON qci.quality_case_id=qc.id
      JOIN quality_issues qi ON qi.id=qci.quality_issue_id JOIN quality_issue_batches qib ON qib.quality_issue_id=qi.id
      JOIN batches b ON b.id=qib.batch_id JOIN parts p ON p.id=b.part_id JOIN suppliers s ON s.id=b.supplier_id
      WHERE qc.case_number=? AND p.part_number=?
      """,caseNumber,partNumber);
    if(cases.isEmpty()) throw new ResponseStatusException(HttpStatus.NOT_FOUND,"case is not linked to part");
    var vehicles=jdbc.queryForList("""
      SELECT v.model_code AS model,v.name AS name,bi.quantity AS quantity FROM bom_items bi
      JOIN vehicle_models v ON v.id=bi.vehicle_model_id JOIN parts p ON p.id=bi.part_id
      WHERE p.part_number=? AND bi.effective_from<=CURRENT_DATE
        AND (bi.effective_to IS NULL OR bi.effective_to>=CURRENT_DATE)
      """,partNumber);
    var normalized=cases.stream().map(c->Map.of("caseNumber",c.get("caseNumber"),"status",c.get("status"),"issueNumber",c.get("issueNumber"),"severity",c.get("severity"),"batchNumber",c.get("batchNumber"),"supplierCode",c.get("supplierCode"))).toList();
    return Map.of("cases",normalized,"vehicles",vehicles,"part_number",partNumber,"case_number",caseNumber);
  }
  @GetMapping("/review-keys/{key}")
  public Object reviewKey(@PathVariable String key) {
    var rows=jdbc.queryForList("SELECT id,snapshot FROM supplier_risk_reviews WHERE request_key=?",key);
    if(rows.isEmpty())return Map.of();
    try{return Map.of("id",rows.getFirst().get("id"),"snapshot",new com.fasterxml.jackson.databind.ObjectMapper().readTree(rows.getFirst().get("snapshot").toString()));}
    catch(Exception ex){throw new IllegalStateException(ex);}
  }
}
