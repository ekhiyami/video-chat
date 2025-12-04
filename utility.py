import logging
import re
from urllib.parse import urlparse, parse_qs

from youtube_transcript_api import YouTubeTranscriptApi

logger = logging.getLogger()
logger.setLevel("INFO")


def get_video_id_from_url(youtube_url):
    """
    Extract video ID from various YouTube URL formats.
    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - URLs with additional query parameters
    """
    logger.info("Inside get_video_id_from_url ..")
    
    # Try using URL parsing first (most reliable)
    try:
        parsed_url = urlparse(youtube_url)
        
        # Handle youtube.com/watch?v=VIDEO_ID format
        if 'youtube.com' in parsed_url.netloc:
            query_params = parse_qs(parsed_url.query)
            if 'v' in query_params:
                video_id = query_params['v'][0]
                logger.info(f"Extracted video_id via URL parsing: {video_id}")
                return video_id
        
        # Handle youtu.be/VIDEO_ID format
        if 'youtu.be' in parsed_url.netloc:
            video_id = parsed_url.path.strip('/').split('/')[0]
            logger.info(f"Extracted video_id from youtu.be: {video_id}")
            return video_id
        
        # Handle youtube.com/embed/VIDEO_ID format
        if 'youtube.com' in parsed_url.netloc and '/embed/' in parsed_url.path:
            video_id = parsed_url.path.split('/embed/')[1].split('/')[0].split('?')[0]
            logger.info(f"Extracted video_id from embed: {video_id}")
            return video_id
    
    except Exception as e:
        logger.warning(f"URL parsing failed, falling back to regex: {e}")
    
    # Fallback: Use regex pattern matching
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:watch\?v=)([0-9A-Za-z_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            video_id = match.group(1)
            logger.info(f"Extracted video_id via regex: {video_id}")
            return video_id
    
    logger.error(f"Could not extract video ID from URL: {youtube_url}")
    return None


def get_transcript(video_id):
    """
    Retrieve transcript for a YouTube video using the new API.
    The new youtube-transcript-api uses:
    - YouTubeTranscriptApi.list(video_id) to get available transcripts
    - transcript.fetch() to retrieve the actual transcript data
    """
    logger.info(f"Inside get_transcript for video_id: {video_id}")
    
    if not video_id:
        logger.error("No video ID provided")
        return None
    
    try:
        # Get list of available transcripts using the new API
        # Note: The new API requires creating an instance first
        logger.info("Fetching available transcripts...")
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        
        # Try to find English transcript first (manual or auto-generated)
        logger.info("Looking for English transcripts...")
        for transcript_info in transcript_list:
            try:
                # Check if it's an English transcript
                lang_code = getattr(transcript_info, 'language_code', '')
                lang = getattr(transcript_info, 'language', '')
                
                if lang_code.startswith('en') or 'english' in lang.lower():
                    logger.info(f"Found English transcript: {lang} ({lang_code})")
                    transcript_data = transcript_info.fetch()
                    logger.info(f"Successfully retrieved transcript with {len(transcript_data)} segments")
                    return transcript_data
            except Exception as e:
                logger.warning(f"Failed to fetch English transcript: {e}")
                continue
        
        # If no English found, try to translate the first available transcript
        logger.info("No English transcript found, attempting translation...")
        for transcript_info in transcript_list:
            try:
                lang = getattr(transcript_info, 'language', 'unknown')
                logger.info(f"Attempting to translate from {lang}...")
                
                # Try to translate to English
                translated = transcript_info.translate('en')
                transcript_data = translated.fetch()
                logger.info(f"Successfully translated transcript from {lang}")
                return transcript_data
            except Exception as e:
                logger.warning(f"Translation failed: {e}")
                continue
        
        # If we get here, no transcripts could be retrieved
        logger.error("No accessible transcripts found for this video")
        return None
        
    except AttributeError as e:
        logger.error(f"API error - the youtube-transcript-api library may need updating: {e}")
        return None
    
    except Exception as e:
        logger.error(f"Failed to retrieve transcript: {type(e).__name__}: {e}")
        return None

def generate_prompt_from_transcript(transcript):
    """
    Generate a prompt from transcript segments.
    The new API returns FetchedTranscriptSnippet objects with .text, .start, .duration attributes
    """
    logger.info("Inside generate_prompt_from_transcript ..")

    prompt = "Summarize the following video:\n"
    for trans in transcript:
        # Handle both old dict format and new object format for compatibility
        if hasattr(trans, 'text'):
            # New API: FetchedTranscriptSnippet object
            prompt += " " + trans.text
        elif isinstance(trans, dict):
            # Old API: dictionary format
            prompt += " " + trans.get('text', '')
        else:
            # Fallback: try to convert to string
            prompt += " " + str(trans)
    
    logger.info("prompt")
    logger.info(prompt)
    return prompt






