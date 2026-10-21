import json
from pathlib import Path
from functools import lru_cache
from neo4j import GraphDatabase
from .config import settings

MODEL="BAAI/bge-small-en-v1.5"
@lru_cache
def embedding_model():
    from fastembed import TextEmbedding
    return TextEmbedding(model_name=MODEL)
def index_documents(path:Path=Path("data/documents/documents.jsonl")):
    from qdrant_client import QdrantClient, models
    docs=[json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    vectors=list(embedding_model().embed([d["text"] for d in docs]))
    client=QdrantClient(url=settings.qdrant_url)
    client.recreate_collection("factoryops_documents",vectors_config=models.VectorParams(size=len(vectors[0]),distance=models.Distance.COSINE))
    client.upsert("factoryops_documents",[models.PointStruct(id=index,vector=vector.tolist(),payload=doc) for index,(vector,doc) in enumerate(zip(vectors,docs))],wait=True)
    return len(docs)
def sync_golden_graph():
    driver=GraphDatabase.driver(settings.neo4j_uri,auth=(settings.neo4j_user,settings.neo4j_password))
    query="""MERGE (s:Supplier {code:'SUP-001'}) MERGE (p:Part {partNumber:'PART-001'}) MERGE (b:Batch {batchNumber:'BATCH-001'})
    MERGE (a:VehicleModel {modelCode:'VM-A'}) MERGE (c:VehicleModel {modelCode:'VM-B'}) MERGE (i:QualityIssue {issueNumber:'ISSUE-001'})
    MERGE (s)-[:SUPPLIES]->(p) MERGE (b)-[:CONTAINS]->(p) MERGE (a)-[:USES]->(p) MERGE (c)-[:USES]->(p) MERGE (i)-[:AFFECTS]->(b)"""
    try:
        driver.execute_query(query,database_="neo4j")
        driver.execute_query("""
          MATCH (p:Part {partNumber:'PART-001'})
          MERGE (s2:Supplier {code:'SUP-002'}) SET s2.name='Demo Nordic Sensors'
          MERGE (s3:Supplier {code:'SUP-003'}) SET s3.name='Demo Alpine Electronics'
          MERGE (s4:Supplier {code:'SUP-004'}) SET s4.name='Demo Pending Sensors'
          MERGE (s2)-[:SUPPLIES]->(p) MERGE (s3)-[:SUPPLIES]->(p) MERGE (s4)-[:SUPPLIES]->(p)
          MERGE (u:Supplier {code:'UP-DEMO-001'}) SET u.name='Demo Shared Semiconductor Source'
          WITH u,s2 MATCH (s1:Supplier {code:'SUP-001'})
          MERGE (s1)-[:DEPENDS_ON]->(u) MERGE (s2)-[:DEPENDS_ON]->(u)
          """,database_="neo4j")
    finally: driver.close()
