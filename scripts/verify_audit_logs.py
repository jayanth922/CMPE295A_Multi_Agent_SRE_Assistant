
import asyncio
import uuid
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from langchain_core.tools import tool
from loguru import logger

from sre_agent.audit_context import set_audit_context, get_audit_context
from sre_agent.mcp_tool_wrapper import wrap_tool_with_audit
from sre_agent.models import AgentAuditLog, Base
from backend.database import SessionLocal, sync_engine

# Mock Tool
@tool
def sample_tool(arg1: str):
    """A sample tool for testing."""
    return f"Processed {arg1}"

def verify_audit_logging():
    logger.info("Initializing DB tables...")
    Base.metadata.create_all(bind=sync_engine)
    
    # 1. Wrap the tool
    logger.info("Wrapping tool...")
    wrapped_tool = wrap_tool_with_audit(sample_tool)
    
    # 2. Set Context
    incident_id = str(uuid.uuid4())
    agent_name = "TestAgent"
    logger.info(f"Setting context: incident_id={incident_id}, agent_name={agent_name}")
    set_audit_context(incident_id, agent_name)
    
    # 3. Invoke Tool
    logger.info("Invoking tool...")
    result = wrapped_tool.invoke({"arg1": "test_value"})
    logger.info(f"Tool result: {result}")
    
    # 4. Verify DB
    logger.info("Verifying DB...")
    with SessionLocal() as session:
        logs = session.query(AgentAuditLog).filter_by(incident_id=incident_id).all()
        
        if len(logs) == 0:
            logger.error("❌ No audit logs found!")
            sys.exit(1)
            
        log = logs[0]
        logger.info(f"✅ Log found: {log}")
        
        assert log.agent_name == agent_name
        assert log.tool_name == "sample_tool"
        assert "test_value" in log.tool_args
        assert log.status == "SUCCESS"
        assert "Processed test_value" in log.result
        
        logger.info("✅ Verification SUCCESS!")

if __name__ == "__main__":
    verify_audit_logging()
