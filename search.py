import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import random
import concurrent.futures
import re
import html
import json
from urllib.parse import urlparse
from gpt import gpt
from lightweight import chat as lw_chat
class WebResearcher:
    def __init__(self, max_results_per_source=5, timeout=15):
        """
        Initialize the WebResearcher class with expanded parameters.
        
        Args:
            max_results_per_source (int): Maximum number of results to return per source
            timeout (int): Timeout for HTTP requests in seconds
        """
        self.max_results_per_source = max_results_per_source
        self.timeout = timeout
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0"
        ]
    
    def get_random_user_agent(self):
        """Return a random user agent."""
        return random.choice(self.user_agents)
    
    def search_duckduckgo(self, prompt):
        """
        Search DuckDuckGo for information related to a prompt.
        
        Args:
            prompt (str): The search query to look up
            
        Returns:
            list: List of dictionaries containing search results
        """
        query = urllib.parse.quote_plus(prompt)
        url = f"https://html.duckduckgo.com/html/?q={query}"
        
        headers = {
            "User-Agent": self.get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        try:
            # Add a small delay and jitter to avoid rate limiting
            time.sleep(random.uniform(0.5, 1.5))
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            search_results = []
            results = soup.select('.result')
            
            for i, result in enumerate(results):
                if i >= self.max_results_per_source:
                    break
                    
                title_elem = result.select_one('.result__a')
                title = title_elem.get_text().strip() if title_elem else "No title found"
                
                link = None
                if title_elem and 'href' in title_elem.attrs:
                    link = title_elem['href']
                    if 'uddg=' in link:
                        link = urllib.parse.unquote(link.split('uddg=')[1].split('&')[0])
                else:
                    link = "No link found"
                    
                snippet_elem = result.select_one('.result__snippet')
                snippet = snippet_elem.get_text().strip() if snippet_elem else "No snippet found"
                
                # Get domain for the source
                domain = "Unknown"
                if link != "No link found":
                    try:
                        domain = urlparse(link).netloc
                    except:
                        pass
                
                search_results.append({
                    'title': title,
                    'link': link,
                    'snippet': snippet,
                    'source': f'DuckDuckGo ({domain})',
                    'domain': domain
                })
            
            return search_results
            
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
            return []
    
    def search_wikipedia(self, prompt):
        """
        Search Wikipedia for information related to a prompt.
        
        Args:
            prompt (str): The search query
            
        Returns:
            list: List of dictionaries containing search results
        """
        search_url = "https://en.wikipedia.org/w/api.php"
        
        search_params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": prompt,
            "srlimit": self.max_results_per_source,
            "utf8": 1
        }
        
        try:
            search_response = requests.get(search_url, params=search_params, timeout=self.timeout)
            search_response.raise_for_status()
            search_data = search_response.json()
            
            search_results = []
            
            if "query" in search_data and "search" in search_data["query"]:
                for item in search_data["query"]["search"]:
                    page_id = item["pageid"]
                    title = item["title"]
                    snippet = BeautifulSoup(item["snippet"], "html.parser").get_text()
                    
                    # Get more detailed content with the full article text
                    content_params = {
                        "action": "query",
                        "format": "json",
                        "pageids": page_id,
                        "prop": "extracts|info",
                        "explaintext": 1,  # Get plain text content
                        "inprop": "url"
                    }
                    
                    content_response = requests.get(search_url, params=content_params, timeout=self.timeout)
                    content_response.raise_for_status()
                    content_data = content_response.json()
                    
                    page_data = content_data["query"]["pages"][str(page_id)]
                    extract = page_data.get("extract", "No extract available")
                    url = page_data["fullurl"]
                    
                    # Get the first few paragraphs of the extract
                    paragraphs = extract.split('\n\n')
                    intro_extract = '\n\n'.join(paragraphs[:3])  # Get first 3 paragraphs
                    
                    search_results.append({
                        "title": title,
                        "link": url,
                        "snippet": snippet,
                        "extract": intro_extract,
                        "full_extract": extract,
                        'source': 'Wikipedia',
                        'domain': 'wikipedia.org'
                    })
            
            return search_results
            
        except Exception as e:
            print(f"Wikipedia search error: {e}")
            return []
    
    def fetch_page_content(self, url, max_paragraphs=5):
        """
        Fetch and extract main content from a webpage with expanded content.
        
        Args:
            url (str): URL to fetch content from
            max_paragraphs (int): Maximum number of paragraphs to extract
        
        Returns:
            dict: Extracted content and metadata
        """
        if not url or url == "No link found":
            return {"content": "", "metadata": {}}
            
        headers = {"User-Agent": self.get_random_user_agent()}
        
        try:
            # Skip URLs that are likely to be problematic
            if url.endswith(('.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx')):
                return {"content": "Document link (cannot extract text)", "metadata": {"type": "document"}}
                
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Check if we're dealing with HTML content
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' not in content_type:
                return {"content": "Non-HTML content (cannot extract text)", "metadata": {"type": "non-html"}}
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract metadata
            metadata = {
                "title": soup.title.string if soup.title else "No title",
                "url": url,
                "last_modified": response.headers.get('Last-Modified', 'Unknown'),
                "content_type": content_type
            }
            
            # Try to get publication date from meta tags
            for meta in soup.find_all('meta'):
                if meta.get('property') in ['article:published_time', 'og:published_time'] or \
                   meta.get('name') in ['publication_date', 'date']:
                    metadata['publication_date'] = meta.get('content')
                    break
            
            # Remove unwanted elements
            for unwanted in soup.select('script, style, nav, footer, header, aside, .ad, .advertisement, .banner'):
                unwanted.decompose()
            
            # Try to find the main content area
            main_content = None
            for selector in ['main', 'article', '.content', '#content', '.post', '.article', '.entry-content', '#main-content']:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            # If we couldn't find a main content area, use the body
            if not main_content:
                main_content = soup.body
            
            if not main_content:
                return {"content": "", "metadata": metadata}
                
            # Get all paragraphs and headings from the main content
            elements = main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
            
            # Extract text from elements with structure
            content_parts = []
            for i, elem in enumerate(elements):
                if len(content_parts) >= max_paragraphs and elem.name not in ['h1', 'h2', 'h3']:
                    continue  # Skip paragraphs after max_paragraphs, but still include headings
                    
                tag_name = elem.name
                text = elem.get_text().strip()
                
                if not text:
                    continue  # Skip empty elements
                
                # Process based on element type
                if tag_name.startswith('h'):
                    # Add headings with appropriate formatting
                    heading_level = int(tag_name[1])
                    if heading_level <= 3:  # Only include major headings
                        content_parts.append({
                            "type": "heading",
                            "level": heading_level,
                            "text": text
                        })
                elif tag_name == 'p':
                    # Add paragraphs if they're substantial
                    if len(text) > 40:  # Skip very short paragraphs
                        content_parts.append({
                            "type": "paragraph",
                            "text": text
                        })
                elif tag_name == 'li':
                    # Include list items
                    content_parts.append({
                        "type": "list_item",
                        "text": text
                    })
            
            # Format the content structurally
            formatted_content = ""
            for part in content_parts:
                if part["type"] == "heading":
                    formatted_content += f"\n{'#' * part['level']} {part['text']}\n\n"
                elif part["type"] == "paragraph":
                    formatted_content += f"{part['text']}\n\n"
                elif part["type"] == "list_item":
                    formatted_content += f"• {part['text']}\n"
            
            return {"content": formatted_content.strip(), "metadata": metadata}
            
        except Exception as e:
            print(f"Error fetching content from {url}: {e}")
            return {"content": f"Error fetching content: {str(e)}", "metadata": {"error": str(e)}}
    
    def search_news(self, prompt):
        """
        Search for news articles related to the prompt.
        Uses DuckDuckGo with news-specific parameters.
        
        Args:
            prompt (str): The search query
            
        Returns:
            list: List of dictionaries containing news results
        """
        # Append "news" to make the search news-oriented
        news_query = f"{prompt} news"
        query = urllib.parse.quote_plus(news_query)
        
        url = f"https://html.duckduckgo.com/html/?q={query}"
        
        headers = {
            "User-Agent": self.get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        }
        
        try:
            time.sleep(random.uniform(0.5, 1.5))
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            news_results = []
            
            # Look for news-like results
            results = soup.select('.result')
            for i, result in enumerate(results):
                if i >= self.max_results_per_source:
                    break
                
                title_elem = result.select_one('.result__a')
                title = title_elem.get_text().strip() if title_elem else "No title found"
                
                # Skip if not news-like
                if not any(news_term in title.lower() for news_term in ['news', 'report', 'announce', 'update', 'latest']):
                    # Still include if domain seems news-like
                    link = None
                    if title_elem and 'href' in title_elem.attrs:
                        link = title_elem['href']
                        if 'uddg=' in link:
                            link = urllib.parse.unquote(link.split('uddg=')[1].split('&')[0])
                            domain = urlparse(link).netloc
                            if not any(news_domain in domain for news_domain in [
                                'news', 'reuters', 'bbc', 'cnn', 'nytimes', 'guardian', 'wsj', 'washington', 
                                'forbes', 'ap', 'npr', 'aljazeera', 'bloomberg'
                            ]):
                                continue  # Skip if not a news domain
                    else:
                        continue  # Skip if no link
                
                snippet_elem = result.select_one('.result__snippet')
                snippet = snippet_elem.get_text().strip() if snippet_elem else "No snippet found"
                
                if link and link != "No link found":
                    try:
                        domain = urlparse(link).netloc
                    except:
                        domain = "Unknown"
                else:
                    continue  # Skip if no valid link
                
                news_results.append({
                    'title': title,
                    'link': link,
                    'snippet': snippet,
                    'source': f'News ({domain})',
                    'domain': domain
                })
            
            return news_results
            
        except Exception as e:
            print(f"News search error: {e}")
            return []
    
    def research(self, prompt, fetch_content=True, news=True):
        """
        Perform comprehensive research on a prompt using multiple sources.
        
        Args:
            prompt (str): The search query
            fetch_content (bool): Whether to fetch actual content from result URLs
            news (bool): Whether to include news results
            
        Returns:
            dict: Combined search results with metadata
        """
        print(f"Researching: {prompt}")
        start_time = time.time()
        
        # Use concurrent.futures to run searches in parallel
        futures = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Submit search tasks
            futures.append(executor.submit(self.search_duckduckgo, prompt))
            futures.append(executor.submit(self.search_wikipedia, prompt))
            if news:
                futures.append(executor.submit(self.search_news, prompt))
            
            # Get results
            all_results = []
            for future in concurrent.futures.as_completed(futures):
                all_results.extend(future.result())
        
        print(f"Found {len(all_results)} total results")
        
        # Deduplicate results based on URL and title similarity
        deduplicated_results = []
        seen_urls = set()
        seen_title_sigs = set()
        
        for result in all_results:
            # Normalize the URL
            url = result.get('link', '')
            if url and url != "No link found":
                # Remove tracking parameters and normalize
                url_parts = url.split('?')[0].split('#')[0].lower().rstrip('/')
                if url_parts in seen_urls:
                    continue
                seen_urls.add(url_parts)
            
            # Check for very similar titles
            title = result.get('title', '')
            title_sig = ''.join(word.lower()[:4] for word in re.findall(r'\w+', title) if len(word) > 3)
            if len(title_sig) > 0 and title_sig in seen_title_sigs:
                continue
            if len(title_sig) > 0:
                seen_title_sigs.add(title_sig)
            
            deduplicated_results.append(result)
        
        print(f"After deduplication: {len(deduplicated_results)} results")
        
        # Fetch additional content if requested
        if fetch_content:
            print("Fetching additional content from URLs...")
            
            # Use ThreadPoolExecutor to fetch content in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_result = {}
                
                # Submit content fetching tasks
                for i, result in enumerate(deduplicated_results):
                    if i < 8:  # Limit to first 8 results to avoid overwhelming
                        url = result.get('link')
                        if url and url != "No link found":
                            future = executor.submit(self.fetch_page_content, url)
                            future_to_result[future] = result
                
                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_result):
                    result = future_to_result[future]
                    try:
                        content_data = future.result()
                        result['content'] = content_data["content"]
                        result['content_metadata'] = content_data["metadata"]
                    except Exception as e:
                        print(f"Error fetching content: {e}")
                        result['content'] = f"Error fetching content: {str(e)}"
                        result['content_metadata'] = {"error": str(e)}
        
        # Add contextual info to Wikipedia results
        for result in deduplicated_results:
            if result.get('source') == 'Wikipedia' and 'full_extract' in result:
                # Keep the full extract but prioritize it differently
                result['detailed_content'] = result['full_extract']
        
        end_time = time.time()
        
        return {
            'query': prompt,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'results': deduplicated_results,
            'result_count': len(deduplicated_results),
            'execution_time': round(end_time - start_time, 2)
        }
    
    def format_results(self, research_data, detailed=True, max_length=None):
        """
        Format research results into a readable string with expanded content.
        
        Args:
            research_data (dict): Research data from the research method
            detailed (bool): Whether to include detailed content
            max_length (int): Maximum length of the formatted output
            
        Returns:
            str: Formatted research results
        """
        if not research_data or not research_data['results']:
            return f"No information found for: '{research_data['query']}'"
        
        formatted_output = f"Research results for: '{research_data['query']}'\n"
        formatted_output += f"Time: {research_data['timestamp']} (took {research_data['execution_time']}s)\n"
        formatted_output += f"Found {research_data['result_count']} unique results\n\n"
        
        # Group results by source type
        results_by_type = {
            'Wikipedia': [],
            'News': [],
            'Web': []
        }
        
        for result in research_data['results']:
            source = result.get('source', '')
            if 'Wikipedia' in source:
                results_by_type['Wikipedia'].append(result)
            elif 'News' in source:
                results_by_type['News'].append(result)
            else:
                results_by_type['Web'].append(result)
        
        # Process Wikipedia results first (usually most informative)
        if results_by_type['Wikipedia']:
            formatted_output += "=== WIKIPEDIA RESULTS ===\n\n"
            for i, result in enumerate(results_by_type['Wikipedia'], 1):
                formatted_output += f"{i}. {result['title']}\n"
                formatted_output += f"   URL: {result['link']}\n\n"
                
                # Include Wikipedia extract (more comprehensive)
                if detailed and 'extract' in result:
                    extract = result['extract']
                    formatted_output += f"{extract}\n\n"
                elif 'snippet' in result:
                    formatted_output += f"   {result['snippet']}\n\n"
        
        # Process News results next
        if results_by_type['News']:
            formatted_output += "=== NEWS RESULTS ===\n\n"
            for i, result in enumerate(results_by_type['News'], 1):
                formatted_output += f"{i}. {result['title']} [{result.get('domain', 'Unknown')}]\n"
                formatted_output += f"   URL: {result['link']}\n"
                formatted_output += f"   {result['snippet']}\n\n"
                
                # Include content if available and detailed mode is on
                if detailed and 'content' in result and result['content']:
                    # Format and limit the content preview
                    content = result['content']
                    if len(content) > 800:  # Larger preview for news
                        preview = content[:800].replace('\n\n', '\n') + "...\n"
                    else:
                        preview = content.replace('\n\n', '\n') + "\n"
                    
                    formatted_output += "   --- Content Preview ---\n"
                    formatted_output += f"   {preview}\n"
                
                formatted_output += "\n"
        
        # Process Web results last
        if results_by_type['Web']:
            formatted_output += "=== WEB RESULTS ===\n\n"
            for i, result in enumerate(results_by_type['Web'], 1):
                formatted_output += f"{i}. {result['title']} [{result.get('domain', 'Unknown')}]\n"
                formatted_output += f"   URL: {result['link']}\n"
                formatted_output += f"   {result['snippet']}\n\n"
                
                # Include content if available and detailed mode is on
                if detailed and 'content' in result and result['content']:
                    # Format and limit the content preview
                    content = result['content']
                    if len(content) > 500:  # Medium preview for web content
                        preview = content[:500].replace('\n\n', '\n') + "...\n"
                    else:
                        preview = content.replace('\n\n', '\n') + "\n"
                    
                    formatted_output += "   --- Content Preview ---\n"
                    formatted_output += f"   {preview}\n"
                
                formatted_output += "\n"
        
        # Limit overall length if specified
        if max_length and len(formatted_output) > max_length:
            formatted_output = formatted_output[:max_length - 100] + "...\n\n[Output truncated due to length]\n"
        
        return formatted_output
    
    def get_data_for_analysis(self, research_data):
        """
        Get research data in a structured format for further analysis.
        
        Args:
            research_data (dict): Research data from the research method
            
        Returns:
            dict: Data structured for analysis
        """
        return {
            'query': research_data['query'],
            'timestamp': research_data['timestamp'],
            'results': research_data['results'],
            'result_count': research_data['result_count'],
            'sources': {
                'wikipedia': [r for r in research_data['results'] if 'Wikipedia' in r.get('source', '')],
                'news': [r for r in research_data['results'] if 'News' in r.get('source', '')],
                'web': [r for r in research_data['results'] if 'Wikipedia' not in r.get('source', '') and 'News' not in r.get('source', '')]
            }
        }

def get_information(prompt, fetch_full_content=True, detailed=True, max_length=None):
    """
    Get comprehensive information for a prompt from multiple sources.
    Enhanced version with more content and better formatting.
    
    Args:
        prompt (str): The prompt to research
        fetch_full_content (bool): Whether to fetch the full content from result URLs
        detailed (bool): Whether to include detailed content in the output
        max_length (int): Maximum length of the output (None for unlimited)
        
    Returns:
        str: Formatted research results
    """
    researcher = WebResearcher(max_results_per_source=5)
    research_data = researcher.research(prompt, fetch_content=fetch_full_content, news=True)
    return researcher.format_results(research_data, detailed=detailed, max_length=max_length)

def analyze_and_summarize(prompt, fetch_full_content=True):
    """
    Analyze and provide a concise summary of information related to the prompt.
    
    Args:
        prompt (str): The prompt to research
        fetch_full_content (bool): Whether to fetch the full content
        
    Returns:
        dict: Research data and summary
    """
    researcher = WebResearcher(max_results_per_source=5)
    research_data = researcher.research(prompt, fetch_content=fetch_full_content, news=True)
    
    # Get the detailed results for use in downstream applications
    structured_data = researcher.get_data_for_analysis(research_data)
    
    # Return both the raw data and formatted results
    return {
        'raw_data': structured_data,
        'formatted_results': researcher.format_results(research_data, detailed=True, max_length=None)
    }

def search(prompt):
    information=get_information(prompt)
    summary=gpt(f"You are a helpful text summarizer. Please as briefly as possible, without losing any information, summarize this text: {information}")
    
    second_prompt=gpt(f"Take the central theme of this information and turn it into a key word optimized google search to help find information related to what the the central theme. You may only return the new query in your response, nothing else. : \n {summary}")
    new_information=get_information(second_prompt)
    
    second_take=gpt(f"You are a helpful text summarizer. Please as briefly as possible, without losing any information, summarize this text:  {new_information} {summary}")
    return second_take

def chat(prompt):
    info=search(prompt)
    formatted_prompt = f"""
    You are a helpful AI assistant. Based on the following contextual information, 
    please provide a clear, accurate, and concise response to the user's question.
    
    USER QUESTION:
    {prompt}
    
    CONTEXTUAL INFORMATION:
    ''{info}''
    
    Instructions:
    1. Use only the information provided above to answer the question
    2. If the information is insufficient, acknowledge the limitations BRIEFLY and move on
    3. Format your response in a readable manner in text paragraph format
    5. Keep your response focused and relevant to the question
    """
    
    return lw_chat(formatted_prompt, model_name="meta-llama/Llama-3.2-3B-Instruct")