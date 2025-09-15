from pocketflow import AsyncParallelBatchNode, Node
from utils.call_llm import call_llm, call_llm_async
from utils.progress import get_progress_tracker
from settings import get_system_config
import asyncio
import logging
import os
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class PruningAgentNode(AsyncParallelBatchNode):
    """Determine if documents are relevant to the query using parallel agents"""
    
    async def prep_async(self, shared):
        unique_documents = shared.get("unique_documents", [])
        user_query = shared.get("user_query", "")
        
        if not unique_documents or not user_query:
            logger.error("Missing documents or query for pruning")
            return []
        
        tracker = get_progress_tracker()
        tracker.update_stage("pruning", 
                           f"Analyzing relevance of {len(unique_documents)} documents",
                           "Running parallel pruning agents")
        tracker.update_pruning(0, len(unique_documents))
        
        return [(doc, user_query) for doc in unique_documents]
    
    async def exec_async(self, doc_and_query):
        document_name, user_query = doc_and_query
        
        # Read the document directly from file
        config = get_system_config()
        doc_path = os.path.join(config.DOCUMENTS_DIR, document_name)
        
        if not os.path.exists(doc_path):
            logger.warning(f"Document not found: {document_name}")
            return (document_name, False, "Document not found")
        
        try:
            with open(doc_path, 'r', encoding='utf-8') as f:
                full_document = f.read()
        except Exception as e:
            logger.error(f"Error reading {document_name}: {e}")
            return (document_name, False, f"Error reading file: {str(e)}")
        
        # Create pruning prompt
        pruning_prompt = f"""You are a legal research assistant. Your task is to determine if a legal case document is relevant to a specific query.

QUERY: {user_query}

DOCUMENT: {document_name}
CONTENT: {full_document[:3000]}{"..." if len(full_document) > 3000 else ""}

INSTRUCTIONS:
1. Carefully analyze if this legal case addresses the issues raised in the query
2. Consider both direct relevance and indirect relevance (precedential value, similar legal principles)
3. For legal research, err on the side of inclusion rather than exclusion
4. Respond with ONLY "YES" or "NO" followed by a brief one-line explanation

RESPONSE FORMAT:
YES/NO - [Brief explanation of relevance/irrelevance]

RESPONSE:"""

        try:
            response = await call_llm_async(pruning_prompt)
            is_relevant = response.strip().upper().startswith("YES")
            
            # Update progress for this completed pruning operation
            tracker = get_progress_tracker()
            current_progress = tracker.get_current_progress()
            total = current_progress.get('total_pruning', 0)
            tracker.increment_pruning(total)
            
            return (document_name, is_relevant, response.strip())
        except Exception as e:
            logger.error(f"Error in pruning agent for {document_name}: {e}")
            
            # Still update progress even on error
            tracker = get_progress_tracker()
            current_progress = tracker.get_current_progress()
            total = current_progress.get('total_pruning', 0)
            tracker.increment_pruning(total)
            
            return (document_name, False, f"Error: {str(e)}")
    
    async def post_async(self, shared, prep_res, exec_res_list):
        pruning_results = {}
        relevant_documents = []
        
        for doc_name, is_relevant, explanation in exec_res_list:
            pruning_results[doc_name] = {
                'relevant': is_relevant,
                'explanation': explanation
            }
            if is_relevant:
                relevant_documents.append(doc_name)
        
        shared["pruning_results"] = pruning_results
        shared["relevant_documents"] = relevant_documents
        
        tracker = get_progress_tracker()
        tracker.update_pruning(len(exec_res_list), len(exec_res_list))
        tracker.update_stage("reading_prep", 
                           f"Selected {len(relevant_documents)} relevant documents",
                           f"Preparing to read {len(relevant_documents)} documents")
        
        logger.info(f"Pruning completed: {len(relevant_documents)}/{len(exec_res_list)} documents relevant")
        return "default"

class ReadingAgentNode(AsyncParallelBatchNode):
    """Extract relevant information from filtered documents using parallel agents"""
    
    async def prep_async(self, shared):
        relevant_documents = shared.get("relevant_documents", [])
        user_query = shared.get("user_query", "")
        
        if not relevant_documents or not user_query:
            logger.error("No relevant documents or query for reading")
            return []
        
        tracker = get_progress_tracker()
        tracker.update_stage("reading", 
                           f"Reading {len(relevant_documents)} documents",
                           "Extracting relevant information")
        tracker.update_reading_start(relevant_documents)
        
        return [(doc, user_query) for doc in relevant_documents]
    
    async def exec_async(self, doc_and_query):
        document_name, user_query = doc_and_query
        
        # Update progress to show this document is being read
        tracker = get_progress_tracker()
        tracker.update_document_status(document_name, "reading")
        
        # Read the document
        config = get_system_config()
        doc_path = os.path.join(config.DOCUMENTS_DIR, document_name)
        
        if not os.path.exists(doc_path):
            logger.warning(f"Document not found: {document_name}")
            tracker.update_document_status(document_name, "error")
            return (document_name, f"Unable to read content for {document_name}")
        
        try:
            with open(doc_path, 'r', encoding='utf-8') as f:
                doc_content = f.read()
        except Exception as e:
            logger.error(f"Error reading {document_name}: {e}")
            tracker.update_document_status(document_name, "error")
            return (document_name, f"Error reading {document_name}: {str(e)}")
        
        # Create reading/extraction prompt
        reading_prompt = f"""You are a legal research assistant. Extract and summarize all information relevant to the user's query from this legal case.

USER QUERY: {user_query}

LEGAL CASE: {document_name}
FULL CONTENT: {doc_content}

INSTRUCTIONS:
1. Identify all sections, paragraphs, and legal principles relevant to the query
2. Extract key facts, legal reasoning, and conclusions
3. Include relevant quotes with specific references
4. Organize information clearly and concisely
5. If the case sets precedent or cites other relevant cases, include that information

PROVIDE A STRUCTURED SUMMARY:

**Case Overview:**
[Brief description of the case and its relevance to the query]

**Key Facts:**
[Relevant factual circumstances]

**Legal Issues:**
[Legal questions addressed that relate to the query]

**Court's Analysis:**
[How the court analyzed the issues relevant to your query]

**Decision/Outcome:**
[The court's decision on relevant issues]

**Precedential Value:**
[How this case might apply to similar situations]

**Relevant Quotes:**
[Direct quotes from the decision with paragraph references if available]

SUMMARY:"""

        try:
            # Use async LLM call for true parallel execution
            response = await call_llm_async(reading_prompt)
            
            # Update progress to show this document is completed
            tracker.update_document_status(document_name, "completed")
            tracker.increment_reading(document_name)
            
            return (document_name, response)
        except Exception as e:
            logger.error(f"Error in reading agent for {document_name}: {e}")
            
            # Update status to error
            tracker.update_document_status(document_name, "error")
            tracker.increment_reading(document_name)
            
            return (document_name, f"Error reading {document_name}: {str(e)}")
    
    async def post_async(self, shared, prep_res, exec_res_list):
        document_summaries = {}
        for doc_name, summary in exec_res_list:
            document_summaries[doc_name] = summary
        
        shared["document_summaries"] = document_summaries
        
        tracker = get_progress_tracker()
        tracker.update_stage("aggregation", 
                           "Synthesizing findings",
                           "Preparing comprehensive response")
        
        logger.info(f"Reading completed for {len(document_summaries)} documents")
        return "default"

class AggregationAgentNode(Node):
    """Combine all information into final comprehensive response"""
    
    def prep(self, shared):
        user_query = shared.get("user_query", "")
        document_summaries = shared.get("document_summaries", {})
        return (user_query, document_summaries)
    
    def exec(self, prep_data):
        user_query, document_summaries = prep_data
        
        tracker = get_progress_tracker()
        tracker.update_aggregation()
        
        if not document_summaries:
            return "I apologize, but I could not find any relevant legal cases for your query. Please try rephrasing your question or providing more specific details."
        
        # Create aggregation prompt
        all_summaries = "\n\n" + "="*50 + "\n\n".join([
            f"CASE: {doc_name}\n{summary}" 
            for doc_name, summary in document_summaries.items()
        ])
        
        aggregation_prompt = f"""You are a legal research assistant providing a comprehensive response based on relevant case law.

USER QUERY: {user_query}

RELEVANT LEGAL CASES AND SUMMARIES:
{all_summaries}

INSTRUCTIONS:
1. Synthesize the information from all relevant cases
2. Provide a comprehensive answer to the user's query
3. Cite specific cases and their holdings
4. Identify patterns, trends, or conflicts between cases
5. Highlight the most authoritative or recent precedents
6. Ensure all information is grounded in the provided case law
7. Do not add information not found in the cases
8. Structure your response clearly and professionally

PROVIDE A COMPREHENSIVE LEGAL RESEARCH RESPONSE:

**Executive Summary:**
[Brief overview of findings relevant to the query]

**Relevant Legal Principles:**
[Key legal principles established by the cases]

**Case Analysis:**
[Analysis of how the cases address the query, organized by theme or principle]

**Practical Applications:**
[How these cases might apply to situations described in the query]

**Conclusion:**
[Summary of the legal position based on the case law reviewed]

**Cases Cited:**
[List of all cases referenced with brief descriptions of their relevance]

COMPREHENSIVE RESPONSE:"""

        try:
            response = call_llm(aggregation_prompt)
            return response
        except Exception as e:
            logger.error(f"Error in aggregation: {e}")
            return f"I apologize, but there was an error synthesizing the legal research results: {str(e)}"
    
    def post(self, shared, prep_res, exec_res):
        shared["final_response"] = exec_res
         
        tracker = get_progress_tracker()
        tracker.complete_session(True, "Legal research completed successfully")
        
        logger.info("Legal research process completed successfully")
        return "default"
 