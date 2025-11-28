"""
VALORA CrewAI API Router
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from ..crew.orchestrator import CrewOrchestrator
from ..simulation.orchestrator import SimulationManager

router = APIRouter()

simulation_manager = SimulationManager()

# Task tracking
analysis_tasks: Dict[str, Dict] = {}


class AnalysisRequest(BaseModel):
    """Request for economic analysis"""
    simulation_id: str
    analysis_type: str = Field(..., pattern="^(economic|policy|forecast|report)$")
    context: Optional[str] = None
    parameters: Dict[str, Any] = {}


class PolicyBriefRequest(BaseModel):
    """Request for policy brief"""
    simulation_id: str
    topic: str
    target_audience: str = "general"  # general, technical, executive
    include_recommendations: bool = True


class DebateRequest(BaseModel):
    """Request for policy debate"""
    simulation_id: str
    policy_question: str
    perspectives: List[str] = ["keynesian", "monetarist", "austrian"]


class TaskResponse(BaseModel):
    """Async task response"""
    task_id: str
    status: str
    created_at: str


class AnalysisResult(BaseModel):
    """Analysis result"""
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


async def run_analysis(task_id: str, crew: CrewOrchestrator, analysis_type: str, 
                       context: Dict[str, Any], parameters: Dict[str, Any]):
    """Run analysis in background"""
    try:
        analysis_tasks[task_id]['status'] = 'running'
        
        if analysis_type == 'economic':
            result = await crew.analyze_economic_state(context)
        elif analysis_type == 'policy':
            result = await crew.generate_policy_recommendations(context, parameters.get('targets', {}))
        elif analysis_type == 'forecast':
            result = await crew.generate_forecast(context, parameters.get('horizon', 20))
        elif analysis_type == 'report':
            result = await crew.generate_report(context, parameters.get('format', 'detailed'))
        else:
            result = {"error": "Unknown analysis type"}
        
        analysis_tasks[task_id]['status'] = 'completed'
        analysis_tasks[task_id]['result'] = result
        analysis_tasks[task_id]['completed_at'] = datetime.utcnow().isoformat()
        
    except Exception as e:
        analysis_tasks[task_id]['status'] = 'failed'
        analysis_tasks[task_id]['error'] = str(e)
        analysis_tasks[task_id]['completed_at'] = datetime.utcnow().isoformat()


@router.post("/analyze", response_model=TaskResponse)
async def request_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
):
    """Request economic analysis (async)"""
    sim = simulation_manager.get_simulation(request.simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.engine:
        raise HTTPException(status_code=400, detail="Simulation not initialized")
    
    # Create task
    task_id = str(uuid.uuid4())
    analysis_tasks[task_id] = {
        'task_id': task_id,
        'status': 'pending',
        'result': None,
        'error': None,
        'created_at': datetime.utcnow().isoformat(),
        'completed_at': None
    }
    
    # Build context
    context = {
        'current_state': sim.engine.state.to_dict(),
        'history': sim.history[-50:] if sim.history else [],
        'user_context': request.context
    }
    
    # Create crew orchestrator
    crew = CrewOrchestrator()
    
    # Run in background
    background_tasks.add_task(
        run_analysis,
        task_id,
        crew,
        request.analysis_type,
        context,
        request.parameters
    )
    
    return TaskResponse(
        task_id=task_id,
        status='pending',
        created_at=analysis_tasks[task_id]['created_at']
    )


@router.get("/analyze/{task_id}", response_model=AnalysisResult)
async def get_analysis_result(task_id: str):
    """Get analysis result"""
    if task_id not in analysis_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = analysis_tasks[task_id]
    return AnalysisResult(**task)


@router.post("/analyze-sync")
async def analyze_sync(request: AnalysisRequest):
    """Request synchronous economic analysis"""
    sim = simulation_manager.get_simulation(request.simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.engine:
        raise HTTPException(status_code=400, detail="Simulation not initialized")
    
    context = {
        'current_state': sim.engine.state.to_dict(),
        'history': sim.history[-20:] if sim.history else [],
        'user_context': request.context
    }
    
    crew = CrewOrchestrator()
    
    try:
        if request.analysis_type == 'economic':
            result = await crew.analyze_economic_state(context)
        elif request.analysis_type == 'policy':
            result = await crew.generate_policy_recommendations(
                context, 
                request.parameters.get('targets', {})
            )
        elif request.analysis_type == 'forecast':
            result = await crew.generate_forecast(
                context,
                request.parameters.get('horizon', 20)
            )
        elif request.analysis_type == 'report':
            result = await crew.generate_report(
                context,
                request.parameters.get('format', 'detailed')
            )
        else:
            raise HTTPException(status_code=400, detail="Unknown analysis type")
        
        return {
            "simulation_id": request.simulation_id,
            "analysis_type": request.analysis_type,
            "result": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/policy-brief")
async def generate_policy_brief(request: PolicyBriefRequest):
    """Generate a policy brief"""
    sim = simulation_manager.get_simulation(request.simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.engine:
        raise HTTPException(status_code=400, detail="Simulation not initialized")
    
    crew = CrewOrchestrator()
    
    context = {
        'current_state': sim.engine.state.to_dict(),
        'topic': request.topic,
        'target_audience': request.target_audience
    }
    
    try:
        brief = await crew.generate_policy_brief(
            context,
            include_recommendations=request.include_recommendations
        )
        
        return {
            "simulation_id": request.simulation_id,
            "topic": request.topic,
            "brief": brief
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/debate")
async def generate_policy_debate(request: DebateRequest):
    """Generate multi-perspective policy debate"""
    sim = simulation_manager.get_simulation(request.simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.engine:
        raise HTTPException(status_code=400, detail="Simulation not initialized")
    
    crew = CrewOrchestrator()
    
    context = {
        'current_state': sim.engine.state.to_dict(),
        'policy_question': request.policy_question
    }
    
    try:
        debate = await crew.generate_debate(context, request.perspectives)
        
        return {
            "simulation_id": request.simulation_id,
            "question": request.policy_question,
            "debate": debate
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def list_crew_agents():
    """List available CrewAI agents"""
    return {
        "agents": [
            {
                "name": "Economic Analyst",
                "role": "Analyzes macroeconomic conditions and trends",
                "capabilities": ["trend_analysis", "indicator_interpretation", "cycle_detection"]
            },
            {
                "name": "Policy Advisor",
                "role": "Recommends monetary and fiscal policies",
                "capabilities": ["policy_design", "impact_assessment", "tradeoff_analysis"]
            },
            {
                "name": "Risk Analyst",
                "role": "Identifies and assesses economic risks",
                "capabilities": ["risk_identification", "stress_testing", "scenario_analysis"]
            },
            {
                "name": "Forecaster",
                "role": "Generates economic forecasts",
                "capabilities": ["time_series_forecasting", "scenario_projection", "confidence_intervals"]
            },
            {
                "name": "Report Writer",
                "role": "Synthesizes analysis into reports",
                "capabilities": ["technical_writing", "executive_summaries", "visualization_design"]
            }
        ]
    }


@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200)
):
    """List analysis tasks"""
    tasks = list(analysis_tasks.values())
    
    if status:
        tasks = [t for t in tasks if t['status'] == status]
    
    # Sort by created_at descending
    tasks = sorted(tasks, key=lambda x: x['created_at'], reverse=True)[:limit]
    
    return {"tasks": tasks}


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task"""
    if task_id not in analysis_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    del analysis_tasks[task_id]
    return {"message": "Task deleted"}


@router.post("/chat")
async def chat_with_crew(
    simulation_id: str,
    message: str,
    conversation_id: Optional[str] = None
):
    """Chat with CrewAI about the simulation"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.engine:
        raise HTTPException(status_code=400, detail="Simulation not initialized")
    
    crew = CrewOrchestrator()
    
    context = {
        'current_state': sim.engine.state.to_dict(),
        'history': sim.history[-10:] if sim.history else [],
        'user_message': message
    }
    
    try:
        response = await crew.chat(context, conversation_id)
        
        return {
            "simulation_id": simulation_id,
            "message": message,
            "response": response['message'],
            "conversation_id": response.get('conversation_id', conversation_id or str(uuid.uuid4()))
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain/{simulation_id}")
async def explain_state(simulation_id: str, aspect: Optional[str] = None):
    """Get natural language explanation of simulation state"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.engine:
        raise HTTPException(status_code=400, detail="Simulation not initialized")
    
    crew = CrewOrchestrator()
    
    context = {
        'current_state': sim.engine.state.to_dict(),
        'aspect': aspect  # e.g., 'inflation', 'unemployment', 'policy'
    }
    
    try:
        explanation = await crew.explain_state(context)
        
        return {
            "simulation_id": simulation_id,
            "aspect": aspect,
            "explanation": explanation
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
