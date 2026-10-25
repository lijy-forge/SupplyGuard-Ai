from typing import Any
import httpx
from neo4j import GraphDatabase
from .config import settings

class BusinessTools:
    def __init__(self, client: httpx.Client | None=None): self.client=client or httpx.Client(base_url=settings.business_url,timeout=10)
    def get(self,path:str)->dict[str,Any]: r=self.client.get(path); r.raise_for_status(); return r.json()
    def batch_context(self,n:str): return self.get(f"/batches/{n}/context")
    def part_impact(self,n:str): return self.get(f"/parts/{n}/impact")
    def quality_case(self,n:str): return self.get(f"/quality-cases/{n}")
    def create_action(self,n:str,payload:dict): r=self.client.post(f"/quality-cases/{n}/actions",json=payload); r.raise_for_status(); return r.json()
    def batch_supplier(self,case_number:str,part_number:str,batch_number:str)->str|None:
        """Supplier of the batch, taken from the quality case linkage (the batch payload hides it)."""
        r=self.client.get("/supplier-risk/context",params={"partNumber":part_number,"caseNumber":case_number}); r.raise_for_status()
        rows=r.json().get("cases",[])
        return next((r["supplierCode"] for r in rows if r.get("batchNumber")==batch_number),None)

class GraphTools:
    def impact(self,part_number:str)->list[dict]:
        driver=GraphDatabase.driver(settings.neo4j_uri,auth=(settings.neo4j_user,settings.neo4j_password))
        try:
            q="MATCH (p:Part {partNumber:$part})<-[:USES]-(v:VehicleModel) RETURN v.modelCode AS model, v.name AS name"
            return [dict(x) for x in driver.execute_query(q,part=part_number,database_="neo4j").records]
        finally: driver.close()
    def batch_impact(self,batch_number:str)->list[dict]:
        driver=GraphDatabase.driver(settings.neo4j_uri,auth=(settings.neo4j_user,settings.neo4j_password))
        try:
            q="MATCH (b:Batch {batchNumber:$batch})-[:CONTAINS]->(:Part)<-[:USES]-(v:VehicleModel) RETURN v.modelCode AS model, v.name AS name"
            return [dict(x) for x in driver.execute_query(q,batch=batch_number,database_="neo4j").records]
        finally: driver.close()
    def supplier_dependency(self,supplier_code:str)->list[dict]:
        driver=GraphDatabase.driver(settings.neo4j_uri,auth=(settings.neo4j_user,settings.neo4j_password))
        try:
            q="MATCH (s:Supplier {code:$supplier})-[:SUPPLIES]->(p:Part) RETURN p.partNumber AS part, p.name AS name"
            return [dict(x) for x in driver.execute_query(q,supplier=supplier_code,database_="neo4j").records]
        finally: driver.close()

    def risk_context(self, part_number: str, current_supplier: str) -> dict:
        from neo4j import Query
        driver=GraphDatabase.driver(settings.neo4j_uri,auth=(settings.neo4j_user,settings.neo4j_password),connection_timeout=5,connection_acquisition_timeout=5)
        try:
            with driver.session(database="neo4j") as session:
                vehicles=[dict(r) for r in session.run(Query("MATCH (p:Part {partNumber:$part})<-[:USES]-(v:VehicleModel) RETURN DISTINCT v.modelCode AS model,v.name AS name",timeout=10),part=part_number)]
                shared=[dict(r) for r in session.run(Query("""
                    MATCH (current:Supplier {code:$current})-[:DEPENDS_ON*1..3]->(u:Supplier)
                    MATCH (candidate:Supplier)-[:SUPPLIES]->(:Part {partNumber:$part})
                    MATCH (candidate)-[:DEPENDS_ON*1..3]->(u)
                    WHERE candidate.code <> $current
                    RETURN DISTINCT candidate.code AS supplier,u.code AS upstream,u.name AS name
                    ORDER BY supplier,upstream LIMIT 100
                    """,timeout=10),part=part_number,current=current_supplier)]
            return {"part_number":part_number,"current_supplier":current_supplier,"vehicles":vehicles,"shared_dependencies":shared}
        finally:
            driver.close()

class DocumentTools:
    def search(self,query:str,limit:int=4)->list[dict]:
        # Load native embedding dependencies only when document search is used.
        from qdrant_client import QdrantClient
        from .indexing import embedding_model
        client=QdrantClient(url=settings.qdrant_url)
        vector=next(embedding_model().embed([query])).tolist()
        points=client.query_points(collection_name="factoryops_documents",query=vector,limit=limit).points
        return [{"id":str(x.payload["id"]),"score":x.score,"text":x.payload.get("text","")} for x in points]
