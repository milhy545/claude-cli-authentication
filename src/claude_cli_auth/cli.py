#!/usr/bin/env python3
"""
Claude CLI Auth - Command Line Interface

Simple CLI tool for testing and basic operations with Claude CLI authentication.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import click

from . import __version__
from .exceptions import ClaudeAuthError
from .facade import ClaudeAuthManager


@click.group()
@click.version_option(version=__version__)
def cli():
    """Claude CLI Authentication - Simple, reliable Claude integration without API keys."""
    pass


@cli.command()
@click.option('--prompt', '-p', required=True, help='Prompt to send to Claude')
@click.option('--session-id', '-s', help='Session ID for conversation continuity')
@click.option('--continue-session', '-c', is_flag=True, help='Continue existing session')
@click.option('--files', '-f', multiple=True, help='Files to include in context')
@click.option('--working-dir', '-w', type=click.Path(exists=True), help='Working directory')
@click.option('--timeout', '-t', type=int, default=30, help='Timeout in seconds (default: 30)')
@click.option('--output', '-o', type=click.Choice(['text', 'json']), default='text', help='Output format')
def query(prompt: str, session_id: Optional[str], continue_session: bool,
          files: tuple, working_dir: Optional[str], timeout: int, output: str):
    """Send a query to Claude using CLI authentication."""
    
    async def run_query():
        try:
            claude = ClaudeAuthManager()
            
            # Prepare arguments
            kwargs = {
                'timeout': timeout
            }
            
            if session_id:
                kwargs['session_id'] = session_id
                kwargs['continue_session'] = continue_session
            
            if files:
                kwargs['files'] = [Path(f) for f in files]
                
            if working_dir:
                kwargs['working_directory'] = Path(working_dir)
            
            # Execute query
            response = await claude.query(prompt, **kwargs)
            
            # Output results
            if output == 'json':
                result = {
                    'success': True,
                    'content': response.content,
                    'session_id': response.session_id,
                    'cost': response.cost,
                    'duration_ms': response.duration_ms,
                    'num_turns': response.num_turns,
                    'tools_used': response.tools_used
                }
                click.echo(json.dumps(result, indent=2))
            else:
                click.echo(response.content)
                if response.cost > 0:
                    click.echo(f"\nCost: ${response.cost:.4f}", err=True)
                if response.session_id:
                    click.echo(f"Session: {response.session_id}", err=True)
            
            await claude.shutdown()
            return True
            
        except ClaudeAuthError as e:
            if output == 'json':
                error_result = {
                    'success': False,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'suggestions': e.suggestions if hasattr(e, 'suggestions') else []
                }
                click.echo(json.dumps(error_result, indent=2))
            else:
                click.echo(f"Claude authentication error: {e}", err=True)
                if hasattr(e, 'suggestions'):
                    for suggestion in e.suggestions:
                        click.echo(f"  • {suggestion}", err=True)
            return False
            
        except Exception as e:
            if output == 'json':
                error_result = {
                    'success': False,
                    'error': str(e),
                    'error_type': type(e).__name__
                }
                click.echo(json.dumps(error_result, indent=2))
            else:
                click.echo(f"Error: {e}", err=True)
            return False
    
    success = asyncio.run(run_query())
    sys.exit(0 if success else 1)


@cli.command()
@click.option('--output', '-o', type=click.Choice(['text', 'json']), default='text', help='Output format')
def status(output: str):
    """Check Claude CLI authentication status."""
    
    async def check_status():
        try:
            claude = ClaudeAuthManager()
            
            # Get authentication status
            is_auth = claude.auth_manager.is_authenticated()
            sessions = claude.list_sessions()
            
            if output == 'json':
                status_info = {
                    'authenticated': is_auth,
                    'sessions': len(sessions),
                    'claude_cli': 'available' if claude.auth_manager._find_claude_cli() else 'not found'
                }
                click.echo(json.dumps(status_info, indent=2))
            else:
                auth_status = "✅ Authenticated" if is_auth else "❌ Not authenticated"
                cli_status = "✅ Available" if claude.auth_manager._find_claude_cli() else "❌ Not found"
                
                click.echo(f"Claude CLI: {cli_status}")
                click.echo(f"Authentication: {auth_status}")
                click.echo(f"Active sessions: {len(sessions)}")
                
                if not is_auth:
                    click.echo("\nTo authenticate, run: claude auth login", err=True)
            
            return is_auth
            
        except Exception as e:
            if output == 'json':
                error_result = {
                    'error': str(e),
                    'authenticated': False
                }
                click.echo(json.dumps(error_result, indent=2))
            else:
                click.echo(f"Status check failed: {e}", err=True)
            return False
    
    success = asyncio.run(check_status())
    sys.exit(0 if success else 1)


@cli.command()
@click.option('--session-id', '-s', help='Specific session ID to show')
@click.option('--output', '-o', type=click.Choice(['text', 'json']), default='text', help='Output format')
def sessions(session_id: Optional[str], output: str):
    """List or show session information."""
    
    try:
        claude = ClaudeAuthManager()
        
        if session_id:
            # Show specific session
            session_info = claude.get_session(session_id)
            if not session_info:
                if output == 'json':
                    click.echo(json.dumps({'error': 'Session not found'}))
                else:
                    click.echo(f"Session '{session_id}' not found", err=True)
                sys.exit(1)
            
            if output == 'json':
                session_data = {
                    'session_id': session_info.session_id,
                    'created_at': session_info.created_at,
                    'last_used': session_info.last_used,
                    'total_cost': session_info.total_cost,
                    'total_turns': session_info.total_turns,
                    'status': session_info.status.value
                }
                click.echo(json.dumps(session_data, indent=2, default=str))
            else:
                click.echo(f"Session: {session_info.session_id}")
                click.echo(f"Created: {session_info.created_at}")
                click.echo(f"Last used: {session_info.last_used}")
                click.echo(f"Cost: ${session_info.total_cost:.4f}")
                click.echo(f"Turns: {session_info.total_turns}")
                click.echo(f"Status: {session_info.status.value}")
        else:
            # List all sessions
            all_sessions = claude.list_sessions()
            
            if output == 'json':
                sessions_data = []
                for session in all_sessions:
                    sessions_data.append({
                        'session_id': session.session_id,
                        'created_at': session.created_at,
                        'last_used': session.last_used,
                        'total_cost': session.total_cost,
                        'total_turns': session.total_turns,
                        'status': session.status.value
                    })
                click.echo(json.dumps(sessions_data, indent=2, default=str))
            else:
                if not all_sessions:
                    click.echo("No sessions found")
                else:
                    click.echo(f"Found {len(all_sessions)} sessions:")
                    for session in all_sessions:
                        click.echo(f"  {session.session_id} - {session.total_turns} turns, ${session.total_cost:.4f}")
        
    except Exception as e:
        if output == 'json':
            click.echo(json.dumps({'error': str(e)}))
        else:
            click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.confirmation_option(prompt='This will remove all expired sessions. Continue?')
def cleanup():
    """Clean up expired sessions."""
    
    async def run_cleanup():
        try:
            claude = ClaudeAuthManager()
            cleaned_count = await claude.cleanup_sessions()
            
            click.echo(f"Cleaned up {cleaned_count} expired sessions")
            return True
            
        except Exception as e:
            click.echo(f"Cleanup failed: {e}", err=True)
            return False
    
    success = asyncio.run(run_cleanup())
    sys.exit(0 if success else 1)


@cli.command()
def test():
    """Test Claude CLI authentication with a simple query."""
    
    async def run_test():
        try:
            click.echo("Testing Claude CLI authentication...")
            
            claude = ClaudeAuthManager()
            
            # Simple test query
            response = await claude.query(
                "Respond with exactly: 'Claude CLI authentication test successful!'",
                timeout=10
            )
            
            if "successful" in response.content:
                click.echo("✅ Test passed!")
                click.echo(f"Response: {response.content}")
                if response.cost > 0:
                    click.echo(f"Cost: ${response.cost:.4f}")
            else:
                click.echo("⚠️  Test completed but unexpected response:")
                click.echo(f"Response: {response.content}")
            
            await claude.shutdown()
            return True
            
        except ClaudeAuthError as e:
            click.echo("❌ Authentication test failed:", err=True)
            click.echo(f"Error: {e}", err=True)
            click.echo("\nTo fix this, run: claude auth login", err=True)
            return False
            
        except Exception as e:
            click.echo("❌ Test failed:", err=True) 
            click.echo(f"Error: {e}", err=True)
            return False
    
    success = asyncio.run(run_test())
    sys.exit(0 if success else 1)


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()