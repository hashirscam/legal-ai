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
            
            return (document_name, is_relevant, response.strip())
        except Exception as e:
            logger.error(f"Error in pruning agent for {document_name}: {e}")
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
        retrieved_chunks = shared.get("retrieved_chunks", [])
        
        if not relevant_documents or not user_query:
            logger.error("No relevant documents or query for reading")
            return []
        
        # Calculate chunk information for each document
        chunk_info = {}
        for doc in relevant_documents:
            # Count total chunks for this document
            doc_chunks = [chunk for chunk in retrieved_chunks 
                         if chunk.get('metadata', {}).get('file_name') == doc]
            total_chunks = len(doc_chunks)
            
            # Count relevant chunks (those that were retrieved)
            relevant_chunks = len(doc_chunks)  # All retrieved chunks are considered relevant
            
            chunk_info[doc] = {
                'total_chunks': total_chunks,
                'relevant_chunks': relevant_chunks
            }
        
        tracker = get_progress_tracker()
        tracker.update_stage("reading", 
                           f"Reading {len(relevant_documents)} documents",
                           "Extracting relevant information")
        tracker.update_reading_start(relevant_documents, chunk_info)
        
        # We'll read metadata directly from files during exec_async
        return [(doc, user_query) for doc in relevant_documents]
    
    async def exec_async(self, doc_and_query):
        document_name, user_query = doc_and_query
        
        # Update progress to show this document is being read
        tracker = get_progress_tracker()
        tracker.update_document_status(document_name, "reading")
        
        # Read the document and extract metadata in one operation
        config = get_system_config()
        doc_path = os.path.join(config.DOCUMENTS_DIR, document_name)
        
        if not os.path.exists(doc_path):
            logger.warning(f"Document not found: {document_name}")
            tracker.update_document_status(document_name, "error")
            return (document_name, f"Unable to read content for {document_name}", {})
        
        try:
            # Single file read and metadata extraction
            from utils.file_processor import create_file_processor
            processor = create_file_processor()
            file_info = processor.process_file(doc_path)
            doc_content = file_info.get('content', '')
            doc_metadata = file_info.get('metadata', {})
            
        except Exception as e:
            logger.error(f"Error reading {document_name}: {e}")
            tracker.update_document_status(document_name, "error")
            return (document_name, f"Error reading {document_name}: {str(e)}", {})
        
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
            
            return (document_name, response, doc_metadata)
        except Exception as e:
            logger.error(f"Error in reading agent for {document_name}: {e}")
            
            # Update status to error
            tracker.update_document_status(document_name, "error")
            tracker.increment_reading(document_name)
            
            return (document_name, f"Error reading {document_name}: {str(e)}", doc_metadata)
    
    async def post_async(self, shared, prep_res, exec_res_list):
        document_summaries = {}
        document_metadata = {}
        
        for result in exec_res_list:
            if len(result) == 3:
                doc_name, summary, metadata = result
                document_summaries[doc_name] = summary
                document_metadata[doc_name] = metadata
            else:
                # Fallback for backward compatibility
                doc_name, summary = result
                document_summaries[doc_name] = summary
                document_metadata[doc_name] = {}
        
        shared["document_summaries"] = document_summaries
        shared["document_metadata"] = document_metadata
        
        logger.info(f"Reading completed for {len(document_summaries)} documents")
        return "default"

class AggregationAgentNode(Node):
    """Combine all information into final comprehensive response"""
    
    def prep(self, shared):
        user_query = shared.get("user_query", "")
        document_summaries = shared.get("document_summaries", {})
        document_metadata = shared.get("document_metadata", {})
        
        # Update progress to show aggregation stage is starting
        tracker = get_progress_tracker()
        tracker.update_aggregation()
        
        return (user_query, document_summaries, document_metadata)
    
    def exec(self, prep_data):
        user_query, document_summaries, document_metadata = prep_data
        
        tracker = get_progress_tracker()
        
        if not document_summaries:
            return "I apologize, but I could not find any relevant legal cases for your query. Please try rephrasing your question or providing more specific details."
        
        # Update progress to show we're building the response
        tracker.update_stage("aggregation", 
                           "Synthesizing findings", 
                           "Building comprehensive legal analysis")
        
        # Build case information with metadata
        case_info_list = []
        citation_map = {}  # Map citations to hyperlinks
        
        for doc_name, summary in document_summaries.items():
            metadata = document_metadata.get(doc_name, {})
            citation = metadata.get('citation', doc_name.replace('.txt', '').replace(' (CanLII)', ''))
            link = metadata.get('link', '')
            
            # Create hyperlink if available
            if link:
                hyperlink = f"[{citation}]({link})"
                citation_map[citation] = hyperlink
            else:
                citation_map[citation] = citation
            
            case_info_list.append({
                'doc_name': doc_name,
                'citation': citation,
                'link': link,
                'summary': summary,
                'hyperlink': citation_map[citation]
            })
        
        # Create the case summaries with hyperlinks
        all_summaries = "\n\n" + "="*50 + "\n\n".join([
            f"CASE: {case['hyperlink']}\nDOCUMENT FILE: {case['doc_name']}\nSUMMARY:\n{case['summary']}" 
            for case in case_info_list
        ])
        
        # Create list of available citations for the LLM
        available_citations = "\n".join([f"- {case['citation']} → {case['hyperlink']}" for case in case_info_list])
        
        aggregation_prompt = f"""You are a senior legal research assistant providing a comprehensive response based on relevant case law. Your response will be displayed in a web interface that supports markdown formatting.

USER QUERY: {user_query}

RELEVANT LEGAL CASES AND SUMMARIES:
{all_summaries}

AVAILABLE CASE CITATIONS WITH HYPERLINKS:
{available_citations}

CRITICAL INSTRUCTIONS:
1. Provide a thorough synthesis of ALL relevant cases
2. When citing cases, use EXACTLY the hyperlink format provided above (e.g., [R. v. Smith, 2025 ONCJ 123](https://canlii.ca/link))
3. Always use the EXACT hyperlink format from the "AVAILABLE CASE CITATIONS" list when mentioning any case
4. Your response will be rendered as markdown, so hyperlinks will be clickable
5. Structure your response professionally with clear headings using markdown (##, ###)
6. Use bullet points and formatting to make it easy to read
7. Include specific paragraph references where available
8. Ground ALL statements in the provided case law

REQUIRED STRUCTURE (use markdown formatting):

## 📋 Executive Summary
Provide a comprehensive overview directly answering the user's query, citing key cases with hyperlinks.

## ⚖️ Legal Framework

### Applicable Legal Principles
List and explain key legal principles, citing cases with hyperlinks.

### Statutory Context
Note relevant statutes mentioned in the cases.

## 📚 Case Law Analysis

### [Organize by themes - create appropriate headings]
Detailed analysis with case citations using hyperlinks.

## 🔍 Key Findings

### Established Precedents
- Use bullet points with case hyperlinks
- Clear legal rules from the cases

### Factual Distinctions
Important differences between cases.

## 💡 Practical Implications
How these precedents apply to similar situations.

## 🎯 Conclusion
Synthesized legal position based on all cases reviewed.

## 📖 Cases Referenced
List all cases with hyperlinks and brief relevance descriptions.

IMPORTANT NOTE: DON'T MAKE UP LINKS YOURSELF. ONLY ADD THE LINKS THAT ARE PROVIDED IN THE "AVAILABLE CASE CITATIONS" LIST AND THAT TOO ONLY WITH FILE NAMES.

COMPREHENSIVE RESPONSE (in markdown format):"""

        try:
            # Update progress to show we're calling the LLM
            tracker.update_stage("aggregation", 
                               "Synthesizing findings", 
                               "Generating comprehensive legal response")
            
            response = call_llm(aggregation_prompt)
            
            # Add a footer with quick access links
            footer = "\n\n---\n\n### 📑 Quick Case Access\n\n"
            for case in case_info_list:
                footer += f"- {case['hyperlink']}\n"
            
            response += footer
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
 