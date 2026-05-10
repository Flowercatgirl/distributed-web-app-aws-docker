#!/usr/bin/env python3
import sys
import wikipedia

def search_wikipedia(query):
    try:
        search_results = wikipedia.search(query, results=3)
        
        if not search_results:
            return f"No Wikipedia results found for '{query}'"
        
        page = wikipedia.page(search_results[0])
        summary = wikipedia.summary(query, sentences=3)
        
        result = f"**Topic:** {page.title}\n\n"
        result += f"**Summary:** {summary}\n\n"
        result += f"**URL:** {page.url}\n\n"
        result += f"**Related pages:** {', '.join(search_results[1:3]) if len(search_results) > 1 else 'None'}"
        
        return result
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Ambiguous term. Possible options: {', '.join(e.options[:5])}"
    except wikipedia.exceptions.PageError:
        return f"No page found for '{query}'"
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = sys.argv[1]
        print(search_wikipedia(query))
    else:
        print("No query provided")
