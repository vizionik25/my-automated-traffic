from my_automated_traffic.blog_agent import BlogAgent
from my_automated_traffic.bridge_page import QuizPageGenerator
from my_automated_traffic.cli import main_cli, add_offer
from my_automated_traffic.database import DatabaseManager
from my_automated_traffic.social_agent import SocialAgent
from my_automated_traffic.video_agent import VideoAgent

def main() -> None:
    """Console script entrypoint function."""
    main_cli(obj={})

if __name__ == "__main__":
    main()
