"""
VALORA CrewAI Integration
Multi-agent LLM pipeline for economic analysis and policy briefings
"""

import os
import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import CrewAI and LLM clients
try:
    from crewai import Agent, Task, Crew, Process
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    logger.warning("CrewAI not installed. Using mock implementation.")

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


@dataclass
class AnalysisResult:
    """Result from CrewAI analysis"""
    analysis_type: str
    agents_involved: List[str]
    raw_output: str
    structured_output: Dict
    recommendations: List[str]
    risks_identified: List[str]
    confidence_score: float
    timestamp: str
    duration_seconds: float


class LLMProvider:
    """
    Unified LLM provider with fallback support
    """
    
    def __init__(self):
        self.groq_client = None
        self.openai_client = None
        self.active_provider = None
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize available LLM clients"""
        groq_key = os.getenv('GROQ_API_KEY')
        openai_key = os.getenv('OPENAI_API_KEY')
        
        if GROQ_AVAILABLE and groq_key:
            try:
                self.groq_client = Groq(api_key=groq_key)
                self.active_provider = 'groq'
                logger.info("Groq LLM initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq: {e}")
        
        if OPENAI_AVAILABLE and openai_key:
            try:
                self.openai_client = OpenAI(api_key=openai_key)
                if not self.active_provider:
                    self.active_provider = 'openai'
                logger.info("OpenAI LLM initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")
        
        if not self.active_provider:
            logger.warning("No LLM provider available. Using mock responses.")
            self.active_provider = 'mock'
    
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """Generate text using available LLM"""
        
        if self.active_provider == 'groq' and self.groq_client:
            return self._generate_groq(prompt, system_prompt, max_tokens, temperature)
        elif self.active_provider == 'openai' and self.openai_client:
            return self._generate_openai(prompt, system_prompt, max_tokens, temperature)
        else:
            return self._generate_mock(prompt)
    
    def _generate_groq(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int,
        temperature: float
    ) -> str:
        """Generate using Groq"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq generation failed: {e}")
            # Fallback to OpenAI
            if self.openai_client:
                return self._generate_openai(prompt, system_prompt, max_tokens, temperature)
            return self._generate_mock(prompt)
    
    def _generate_openai(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int,
        temperature: float
    ) -> str:
        """Generate using OpenAI"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            return self._generate_mock(prompt)
    
    def _generate_mock(self, prompt: str) -> str:
        """Generate mock response when no LLM available"""
        return f"""
ECONOMIC ANALYSIS REPORT
========================

Based on the provided economic indicators, here is the analysis:

CURRENT STATE ASSESSMENT:
- The economy shows signs of [stable/expanding/contracting] activity
- Key indicators suggest [moderate/low/high] risk levels
- Policy stance appears [appropriate/too tight/too loose]

KEY OBSERVATIONS:
1. GDP growth trajectory indicates [healthy/concerning/stable] momentum
2. Inflation dynamics suggest [anchored/rising/falling] expectations
3. Labor market conditions reflect [tight/slack/balanced] supply-demand

RISK FACTORS:
• Downside: Global slowdown, policy uncertainty
• Upside: Productivity gains, investment recovery

RECOMMENDATIONS:
1. Maintain current policy stance with flexibility
2. Monitor leading indicators for early warning signals
3. Prepare contingency responses for tail risks

CONFIDENCE: 75%

Note: This is a simulated analysis. Connect LLM providers for real AI analysis.
"""


class EconomicAnalyst:
    """Economic analysis agent"""
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
        self.name = "Economic Analyst"
        self.role = "Senior Macroeconomic Analyst"
        self.goal = "Provide comprehensive economic state analysis"
    
    def analyze(self, macro_state: Dict) -> str:
        """Analyze current economic state"""
        system_prompt = """You are a senior macroeconomic analyst at a central bank.
Your role is to provide clear, concise analysis of economic conditions.
Focus on key indicators, trends, and potential risks.
Be specific with numbers and provide actionable insights."""
        
        prompt = f"""Analyze the following economic state and provide a comprehensive assessment:

MACROECONOMIC INDICATORS:
- GDP: ${macro_state.get('gdp', 0):,.0f}
- GDP Growth: {macro_state.get('gdp_growth', 0):.2%}
- Output Gap: {macro_state.get('output_gap', 0):.2%}
- Inflation: {macro_state.get('inflation', 0):.2%}
- Unemployment: {macro_state.get('unemployment', 0):.2%}
- Interest Rate: {macro_state.get('interest_rate', 0):.2%}
- Consumer Confidence: {macro_state.get('consumer_confidence', 100):.1f}
- Business Confidence: {macro_state.get('business_confidence', 100):.1f}
- Debt-to-GDP: {macro_state.get('debt_to_gdp', 0):.1%}
- Business Cycle Phase: {macro_state.get('cycle_phase', 'unknown')}

Provide:
1. Overall economic assessment (2-3 sentences)
2. Key strengths (bullet points)
3. Key concerns (bullet points)
4. Short-term outlook (1-2 sentences)
5. Risk rating (Low/Moderate/Elevated/High)
"""
        return self.llm.generate(prompt, system_prompt)


class TaxPolicyAdvisor:
    """Tax policy analysis agent"""
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
        self.name = "Tax Policy Advisor"
        self.role = "Fiscal Policy Specialist"
        self.goal = "Optimize tax policy for growth and equity"
    
    def analyze(self, macro_state: Dict, current_tax_rate: float) -> str:
        """Analyze tax policy implications"""
        system_prompt = """You are a fiscal policy advisor specializing in taxation.
Your role is to analyze tax policy in the context of economic conditions.
Consider revenue adequacy, growth impact, and distributional effects.
Provide specific, actionable recommendations."""
        
        prompt = f"""Analyze tax policy given current economic conditions:

CURRENT TAX RATE: {current_tax_rate:.1%}
GDP Growth: {macro_state.get('gdp_growth', 0):.2%}
Unemployment: {macro_state.get('unemployment', 0):.2%}
Debt-to-GDP: {macro_state.get('debt_to_gdp', 0):.1%}
Fiscal Deficit: ${macro_state.get('fiscal_deficit', 0):,.0f}
Business Cycle: {macro_state.get('cycle_phase', 'unknown')}

Provide:
1. Assessment of current tax rate appropriateness
2. Impact on economic growth
3. Fiscal sustainability implications
4. Recommended adjustments (if any)
5. Implementation considerations
"""
        return self.llm.generate(prompt, system_prompt)


class RiskAssessor:
    """Risk assessment agent"""
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
        self.name = "Risk Assessor"
        self.role = "Financial Risk Analyst"
        self.goal = "Identify and quantify economic risks"
    
    def analyze(self, macro_state: Dict, bank_metrics: Dict) -> str:
        """Assess systemic risks"""
        system_prompt = """You are a financial stability risk analyst.
Your role is to identify potential risks to economic and financial stability.
Quantify risks where possible and suggest mitigation strategies.
Be specific about trigger conditions and early warning signs."""
        
        prompt = f"""Assess systemic risks in the current environment:

MACROECONOMIC:
- GDP Growth: {macro_state.get('gdp_growth', 0):.2%}
- Inflation: {macro_state.get('inflation', 0):.2%}
- Output Gap: {macro_state.get('output_gap', 0):.2%}

FINANCIAL SECTOR:
- NPL Ratio: {bank_metrics.get('npl_ratio', 0):.2%}
- Capital Ratio: {bank_metrics.get('capital_ratio', 0):.2%}
- Credit Growth: {bank_metrics.get('credit_growth', 0):.2%}

Provide:
1. Top 3 risks with probability and impact assessment
2. Early warning indicators to monitor
3. Recommended stress test scenarios
4. Mitigation strategies for each risk
5. Overall financial stability assessment
"""
        return self.llm.generate(prompt, system_prompt)


class PolicyBriefWriter:
    """Executive briefing generator"""
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
        self.name = "Policy Brief Writer"
        self.role = "Executive Communications Specialist"
        self.goal = "Synthesize analysis into actionable briefs"
    
    def generate_brief(
        self,
        economic_analysis: str,
        tax_analysis: str,
        risk_analysis: str,
        policy_proposal: Optional[Dict] = None
    ) -> str:
        """Generate executive policy brief"""
        system_prompt = """You are an executive communications specialist for policy makers.
Your role is to synthesize complex economic analysis into clear, actionable briefs.
Use clear language, highlight key decisions needed, and prioritize information.
Format for busy executives who need quick comprehension."""
        
        proposal_text = ""
        if policy_proposal:
            proposal_text = f"""
POLICY UNDER CONSIDERATION:
- Name: {policy_proposal.get('name', 'N/A')}
- Type: {policy_proposal.get('category', 'N/A')}
- Description: {policy_proposal.get('description', 'N/A')}
"""
        
        prompt = f"""Synthesize the following analyses into an executive policy brief:

ECONOMIC ANALYSIS:
{economic_analysis}

TAX POLICY ANALYSIS:
{tax_analysis}

RISK ASSESSMENT:
{risk_analysis}

{proposal_text}

Generate a 1-page executive brief with:
1. SITUATION SUMMARY (3 bullet points max)
2. KEY DECISIONS REQUIRED (numbered list)
3. RECOMMENDED ACTIONS (with timeline)
4. RISKS & MITIGATIONS (table format)
5. BOTTOM LINE (1 sentence)
"""
        return self.llm.generate(prompt, system_prompt)


class CrewAIOrchestrator:
    """
    Orchestrates multi-agent analysis workflow
    """
    
    def __init__(self):
        self.llm_provider = LLMProvider()
        
        # Initialize agents
        self.economic_analyst = EconomicAnalyst(self.llm_provider)
        self.tax_advisor = TaxPolicyAdvisor(self.llm_provider)
        self.risk_assessor = RiskAssessor(self.llm_provider)
        self.brief_writer = PolicyBriefWriter(self.llm_provider)
        
        # Analysis history
        self.analysis_history: List[AnalysisResult] = []
    
    def run_full_analysis(
        self,
        macro_state: Dict,
        bank_metrics: Optional[Dict] = None,
        policy_proposal: Optional[Dict] = None
    ) -> AnalysisResult:
        """Run complete multi-agent analysis pipeline"""
        import time
        start_time = time.time()
        
        logger.info("Starting CrewAI full analysis pipeline")
        
        # Default bank metrics if not provided
        if bank_metrics is None:
            bank_metrics = {
                'npl_ratio': 0.02,
                'capital_ratio': 0.12,
                'credit_growth': 0.05
            }
        
        # Stage 1: Economic Analysis
        logger.info("Stage 1: Economic Analysis")
        economic_output = self.economic_analyst.analyze(macro_state)
        
        # Stage 2: Tax Policy Analysis
        logger.info("Stage 2: Tax Policy Analysis")
        tax_output = self.tax_advisor.analyze(
            macro_state,
            macro_state.get('tax_rate', 0.25)
        )
        
        # Stage 3: Risk Assessment
        logger.info("Stage 3: Risk Assessment")
        risk_output = self.risk_assessor.analyze(macro_state, bank_metrics)
        
        # Stage 4: Executive Brief
        logger.info("Stage 4: Executive Brief Generation")
        brief_output = self.brief_writer.generate_brief(
            economic_output,
            tax_output,
            risk_output,
            policy_proposal
        )
        
        duration = time.time() - start_time
        
        # Parse structured output
        structured = self._parse_outputs(
            economic_output, tax_output, risk_output, brief_output
        )
        
        result = AnalysisResult(
            analysis_type="full_analysis",
            agents_involved=[
                self.economic_analyst.name,
                self.tax_advisor.name,
                self.risk_assessor.name,
                self.brief_writer.name
            ],
            raw_output=brief_output,
            structured_output=structured,
            recommendations=structured.get('recommendations', []),
            risks_identified=structured.get('risks', []),
            confidence_score=0.8,
            timestamp=datetime.utcnow().isoformat(),
            duration_seconds=duration
        )
        
        self.analysis_history.append(result)
        logger.info(f"CrewAI analysis completed in {duration:.2f}s")
        
        return result
    
    def _parse_outputs(
        self,
        economic: str,
        tax: str,
        risk: str,
        brief: str
    ) -> Dict:
        """Parse agent outputs into structured format"""
        # Simple parsing - in production, use more sophisticated NLP
        return {
            'economic_summary': economic[:500] if economic else "",
            'tax_summary': tax[:500] if tax else "",
            'risk_summary': risk[:500] if risk else "",
            'executive_brief': brief,
            'recommendations': self._extract_recommendations(brief),
            'risks': self._extract_risks(risk)
        }
    
    def _extract_recommendations(self, text: str) -> List[str]:
        """Extract recommendations from text"""
        recommendations = []
        lines = text.split('\n')
        in_recommendations = False
        
        for line in lines:
            if 'RECOMMEND' in line.upper() or 'ACTION' in line.upper():
                in_recommendations = True
                continue
            if in_recommendations:
                if line.strip().startswith(('-', '•', '*', '1', '2', '3', '4', '5')):
                    recommendations.append(line.strip().lstrip('-•*0123456789. '))
                elif line.strip() == '' or line.strip().isupper():
                    in_recommendations = False
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _extract_risks(self, text: str) -> List[str]:
        """Extract risks from text"""
        risks = []
        lines = text.split('\n')
        
        for line in lines:
            if any(word in line.lower() for word in ['risk', 'threat', 'concern', 'warning']):
                if line.strip().startswith(('-', '•', '*', '1', '2', '3')):
                    risks.append(line.strip().lstrip('-•*0123456789. '))
        
        return risks[:5]
    
    def run_quick_analysis(self, macro_state: Dict) -> str:
        """Run quick economic state analysis only"""
        return self.economic_analyst.analyze(macro_state)
    
    def run_risk_scan(self, macro_state: Dict, bank_metrics: Dict) -> str:
        """Run risk-focused analysis"""
        return self.risk_assessor.analyze(macro_state, bank_metrics)
    
    def get_analysis_history(self, limit: int = 10) -> List[Dict]:
        """Get recent analysis history"""
        return [
            {
                'type': a.analysis_type,
                'timestamp': a.timestamp,
                'duration': a.duration_seconds,
                'recommendations': a.recommendations[:3],
                'confidence': a.confidence_score
            }
            for a in self.analysis_history[-limit:]
        ]


# Global instance
crew_orchestrator = CrewAIOrchestrator()
