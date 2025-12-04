import argparse
import sys

from pathlib import Path


class CommandLineInterface:
    """Handler of command line arguments"""
    
    @staticmethod
    def parse_args():
        """Parsing command line arguments"""
        parser = argparse.ArgumentParser(
            description='Scraper для сайта quotes.toscrape.com',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        parser.add_argument(
            '--pages',
            type=int,
            help='Number of pages to parse (overrides config.json)'
        )
        
        parser.add_argument(
            '--output',
            type=str,
            help='Path to the output file (overrides config.json)'
        )
        
        parser.add_argument(
            '--author',
            type=str,
            help='Name of the author to search for quotes'
        )
        
        parser.add_argument(
            '--config',
            type=str,
            default='config.json',
            help='Path to the configuration file'
        )
        
        return parser.parse_args()
    
    @staticmethod
    def validate_args(args):
        """Validation of command line arguments"""
        if args.pages is not None and args.pages <= 0:
            print("Error: the number of pages must be a positive number")
            sys.exit(1)
        
        if args.output and not args.output.endswith('.json'):
            print("Error: the output file must have a .json extension")
            sys.exit(1)
        
        if not Path(args.config).exists():
            print(f"Error: configuration file {args.config} not found")
            sys.exit(1)
