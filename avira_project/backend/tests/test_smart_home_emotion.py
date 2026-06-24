import sys
import os

# Add directory to import path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.command_processor import CommandProcessor

def main():
    cp = CommandProcessor()
    
    test_cases = [
        "turn on all the lights",
        "switch off the bedroom fan",
        "lock the front door",
        "is the living room light on?",
        "I feel so lonely and sad today", # Should still be emotional/comforting
    ]
    
    print("\n" + "="*60)
    print("  VERIFYING DEVICE COMMAND vs CHITCHAT RESPONSES")
    print("="*60)
    
    for text in test_cases:
        print(f"\n[USER INPUT]: '{text}'")
        result = cp.process(text, language="en")
        print(f"[EMOTION]:    {result.get('emotion')}")
        print(f"[SH CMD]:     {result.get('smart_home_command')}")
        print(f"[RESPONSE]:   {repr(result.get('response'))}")
        print("-" * 60)

if __name__ == "__main__":
    main()
