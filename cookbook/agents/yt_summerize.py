"""
YouTube Video Summarizer: An agent that downloads YouTube videos, transcribes them,
and provides detailed summaries using GPT-4.

Requirements:
- mlx-whisper
- yt-dlp
- ffmpeg

Example Usage:
agent.print_response("Summarize this video: https://www.youtube.com/watch?v=your_video_id")
"""

from pathlib import Path
import yt_dlp
import os
from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.tools.mlx_transcribe import MLXTranscribe
from phi.utils.log import logger

def download_youtube_video(url: str, output_dir: Path) -> str:
    """Download audio from YouTube video and return the local file path."""
    output_file = "audio.mp3"
    full_output_path = output_dir / output_file
    
    print(f"Downloading to directory: {output_dir}")
    print(f"Full output path: {full_output_path}")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': str(output_dir / 'audio'),
        'quiet': False,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'no_warnings': True,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                if info is None:
                    print(f"Error: Could not access video at {url}")
                    return None
                
                print(f"Found video: {info.get('title', 'Unknown title')}")
                
                # Download with fixed filename
                ydl.download([url])
                
                # Check if file exists
                if full_output_path.exists():
                    print(f"File successfully downloaded to: {full_output_path}")
                    return "audio.mp3"  # Return just the filename
                else:
                    print(f"Error: File not found at {full_output_path}")
                    return None
                    
            except yt_dlp.utils.DownloadError as e:
                print(f"Download error: {str(e)}")
                return None
            except Exception as e:
                print(f"Unexpected error during download: {str(e)}")
                return None
                
    except Exception as e:
        print(f"Error initializing yt-dlp: {str(e)}")
        return None

class YouTubeTranscriber(MLXTranscribe):
    def transcribe_youtube(self, url: str) -> str:
        """Download and transcribe a YouTube video."""
        try:
            # Download the video and get the full file path
            print(f"Using base directory: {self.base_dir}")
            file_path = download_youtube_video(url, self.base_dir)
            
            if file_path is None:
                return "Failed to download the video."
            
            # Now transcribe the local file using the full path
            print(f"Attempting to transcribe file at: {file_path}")
            
            # Use Path object to check file existence
            if not Path(file_path).exists():
                return f"Error: File not found at {file_path}"
            
            # Call parent class's transcribe method with just the filename
            return self.transcribe(Path(file_path).name)
            
        except Exception as e:
            return f"Error during transcription: {str(e)}"

# Get audio files from storage/audio directory
phidata_root_dir = Path(__file__).parent.parent.parent.resolve()
audio_storage_dir = phidata_root_dir.joinpath("storage/audio")
if not audio_storage_dir.exists():
    audio_storage_dir.mkdir(exist_ok=True, parents=True)

print(f"Audio storage directory: {audio_storage_dir}")
print(f"Directory exists: {audio_storage_dir.exists()}")
print(f"Directory is writable: {os.access(audio_storage_dir, os.W_OK)}")

# Create the YouTube summarization agent
yt_summary_agent = Agent(
    name="YouTube Summary Agent",
    model=OpenAIChat(
        id="gpt-4",
        system_prompt="""You are an expert at analyzing and summarizing video content.
        When given a transcript, provide a comprehensive summary organized into sections:
        - Main Topics/Key Points
        - Important Details
        - Key Takeaways
        - Notable Quotes (if any)
        
        Make the summary engaging and easy to understand while maintaining accuracy."""
    ),
    tools=[YouTubeTranscriber(base_dir=audio_storage_dir)],
    instructions=[
        "To summarize a YouTube video:",
        "1. Use the `transcribe_youtube` tool with the video URL to get the transcript",
        "2. Analyze the transcript and provide a structured summary",
        "3. Format the response in clear sections using markdown",
    ],
    markdown=True,
)

if __name__ == "__main__":
    # Test with a known public video
    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # This is a very popular public video
    prompt = f"Download, transcribe, and provide a detailed summary of this video: {video_url}"
    yt_summary_agent.print_response(prompt, stream=True)
