from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from smolagents import ToolCallingAgent, GradioUI, LiteLLMModel
from hey_steve.agents_and_tools import *
from hey_steve.rag import *
import os
from dotenv import load_dotenv
load_dotenv()


endpoint = "http://localhost:6006/v1/traces"
trace_provider = TracerProvider()
trace_provider.add_span_processor(
    SimpleSpanProcessor(OTLPSpanExporter(endpoint)))

SmolagentsInstrumentor().instrument(tracer_provider=trace_provider)

model = LiteLLMModel(
    model_id="gemini/gemini-2.0-flash",
    api_key=os.environ['GEMINI_API_KEY'],
)

reranker = Reranker()

steve_rag = SteveRAG(
    collection_name="mc_rag_3",
    ollama_embed_model="nomic-embed-text:latest",
    reranker=reranker)
# steve_rag.load_chunks_into_rag()
retrieverTool = RetrieverTool(steve_rag)


additional_authorized_imports = []

agent = ToolCallingAgent(
    tools=[
        retrieverTool,
        RecipeTool(),
        LootTableTool()
    ],
    model=model,
    add_base_tools=True
)

GradioUI(agent).launch()
