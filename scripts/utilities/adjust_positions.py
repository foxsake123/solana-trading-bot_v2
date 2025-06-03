#!/usr/bin/env python3
"""
Easy Position Size Adjuster for Solana Trading Bot
Allows quick adjustment of position sizes as percentage of balance
"""
import json
import os
from colorama import init, Fore, Style
import sys

# Initialize colorama
init()

class PositionSizeAdjuster:
    def __init__(self):
        self.config_path = "config/trading_params.json"
        self.bot_control_path = "config/bot_control.json"
        self.config = self.load_config()
        self.bot_control = self.load_bot_control()
        
    def load_config(self):
        """Load trading parameters"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except:
            print(f"{Fore.RED}Error loading {self.config_path}{Style.RESET_ALL}")
            return {}
    
    def load_bot_control(self):
        """Load bot control settings"""
        try:
            with open(self.bot_control_path, 'r') as f:
                return json.load(f)
        except:
            print(f"{Fore.RED}Error loading {self.bot_control_path}{Style.RESET_ALL}")
            return {}
    
    def save_configs(self):
        """Save both config files"""
        try:
            # Save trading params
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            
            # Save bot control
            with open(self.bot_control_path, 'w') as f:
                json.dump(self.bot_control, f, indent=4)
                
            print(f"{Fore.GREEN}✅ Configuration saved successfully!{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{Fore.RED}Error saving config: {e}{Style.RESET_ALL}")
            return False
    
    def display_current_settings(self):
        """Display current position size settings"""
        print(f"\n{Fore.CYAN}=== CURRENT POSITION SIZE SETTINGS ==={Style.RESET_ALL}")
        
        # Get values from trading_params.json
        min_pct = self.config.get('min_position_size_pct', 3.0)
        default_pct = self.config.get('default_position_size_pct', 4.0)
        max_pct = self.config.get('max_position_size_pct', 5.0)
        
        # Also check bot_control.json for legacy settings
        legacy_min = self.bot_control.get('min_investment_per_token', 0.1)
        legacy_max = self.bot_control.get('max_investment_per_token', 0.5)
        
        print(f"\n{Fore.YELLOW}Percentage-Based Settings (trading_params.json):{Style.RESET_ALL}")
        print(f"  Minimum: {min_pct}% of balance")
        print(f"  Default: {default_pct}% of balance")
        print(f"  Maximum: {max_pct}% of balance")
        
        # Calculate actual SOL amounts for 10 SOL balance
        print(f"\n{Fore.YELLOW}With 10 SOL balance, this means:{Style.RESET_ALL}")
        print(f"  Minimum: {10 * min_pct / 100:.2f} SOL")
        print(f"  Default: {10 * default_pct / 100:.2f} SOL")
        print(f"  Maximum: {10 * max_pct / 100:.2f} SOL")
        
        print(f"\n{Fore.YELLOW}Legacy Fixed Settings (bot_control.json):{Style.RESET_ALL}")
        print(f"  Min Investment: {legacy_min} SOL")
        print(f"  Max Investment: {legacy_max} SOL")
        print(f"  {Fore.RED}⚠️  These should be removed!{Style.RESET_ALL}")
    
    def update_position_sizes(self):
        """Interactive position size updater"""
        print(f"\n{Fore.CYAN}=== UPDATE POSITION SIZES ==={Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Enter new values as percentage of balance{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Press Enter to keep current value{Style.RESET_ALL}\n")
        
        # Get current values
        current_min = self.config.get('min_position_size_pct', 3.0)
        current_default = self.config.get('default_position_size_pct', 4.0)
        current_max = self.config.get('max_position_size_pct', 5.0)
        
        # Get new values
        try:
            # Minimum
            new_min = input(f"Minimum position size (current: {current_min}%): ").strip()
            if new_min:
                self.config['min_position_size_pct'] = float(new_min)
            
            # Default
            new_default = input(f"Default position size (current: {current_default}%): ").strip()
            if new_default:
                self.config['default_position_size_pct'] = float(new_default)
            
            # Maximum
            new_max = input(f"Maximum position size (current: {current_max}%): ").strip()
            if new_max:
                self.config['max_position_size_pct'] = float(new_max)
            
            # Validate
            min_val = self.config.get('min_position_size_pct', 3.0)
            default_val = self.config.get('default_position_size_pct', 4.0)
            max_val = self.config.get('max_position_size_pct', 5.0)
            
            if not (min_val <= default_val <= max_val):
                print(f"{Fore.RED}Error: Values must be min <= default <= max{Style.RESET_ALL}")
                return False
            
            # Remove legacy settings from bot_control.json
            if 'min_investment_per_token' in self.bot_control:
                del self.bot_control['min_investment_per_token']
            if 'max_investment_per_token' in self.bot_control:
                del self.bot_control['max_investment_per_token']
            
            # Add a flag to use percentage-based sizing
            self.bot_control['use_percentage_sizing'] = True
            
            return True
            
        except ValueError:
            print(f"{Fore.RED}Error: Please enter valid numbers{Style.RESET_ALL}")
            return False
    
    def quick_presets(self):
        """Quick preset options"""
        print(f"\n{Fore.CYAN}=== QUICK PRESETS ==={Style.RESET_ALL}")
        print(f"1. Conservative (2-3-4%)")
        print(f"2. Moderate (3-4-5%) - Current")
        print(f"3. Aggressive (4-5-6%)")
        print(f"4. Very Aggressive (5-7-10%)")
        print(f"5. Custom")
        print(f"0. Cancel")
        
        choice = input(f"\n{Fore.YELLOW}Select preset: {Style.RESET_ALL}").strip()
        
        presets = {
            '1': {'min': 2.0, 'default': 3.0, 'max': 4.0},
            '2': {'min': 3.0, 'default': 4.0, 'max': 5.0},
            '3': {'min': 4.0, 'default': 5.0, 'max': 6.0},
            '4': {'min': 5.0, 'default': 7.0, 'max': 10.0}
        }
        
        if choice in presets:
            self.config['min_position_size_pct'] = presets[choice]['min']
            self.config['default_position_size_pct'] = presets[choice]['default']
            self.config['max_position_size_pct'] = presets[choice]['max']
            
            # Remove legacy settings
            if 'min_investment_per_token' in self.bot_control:
                del self.bot_control['min_investment_per_token']
            if 'max_investment_per_token' in self.bot_control:
                del self.bot_control['max_investment_per_token']
            
            self.bot_control['use_percentage_sizing'] = True
            return True
        elif choice == '5':
            return self.update_position_sizes()
        
        return False
    
    def verify_bot_uses_percentages(self):
        """Check if bot is actually using percentage-based sizing"""
        print(f"\n{Fore.CYAN}=== VERIFYING BOT CONFIGURATION ==={Style.RESET_ALL}")
        
        issues = []
        
        # Check if legacy settings exist
        if 'min_investment_per_token' in self.bot_control:
            issues.append("Legacy 'min_investment_per_token' found in bot_control.json")
        if 'max_investment_per_token' in self.bot_control:
            issues.append("Legacy 'max_investment_per_token' found in bot_control.json")
        
        # Check if percentage settings exist
        if 'min_position_size_pct' not in self.config:
            issues.append("Missing 'min_position_size_pct' in trading_params.json")
        if 'default_position_size_pct' not in self.config:
            issues.append("Missing 'default_position_size_pct' in trading_params.json")
        
        if issues:
            print(f"{Fore.RED}⚠️  Issues found:{Style.RESET_ALL}")
            for issue in issues:
                print(f"  - {issue}")
            print(f"\n{Fore.YELLOW}Fixing these issues...{Style.RESET_ALL}")
            
            # Fix by ensuring percentage settings exist
            if 'min_position_size_pct' not in self.config:
                self.config['min_position_size_pct'] = 3.0
            if 'default_position_size_pct' not in self.config:
                self.config['default_position_size_pct'] = 4.0
            if 'max_position_size_pct' not in self.config:
                self.config['max_position_size_pct'] = 5.0
            
            # Remove legacy settings
            if 'min_investment_per_token' in self.bot_control:
                del self.bot_control['min_investment_per_token']
            if 'max_investment_per_token' in self.bot_control:
                del self.bot_control['max_investment_per_token']
            
            self.bot_control['use_percentage_sizing'] = True
            self.save_configs()
            print(f"{Fore.GREEN}✅ Issues fixed!{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}✅ Configuration looks good!{Style.RESET_ALL}")
    
    def run(self):
        """Main menu"""
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            
            print(f"{Fore.CYAN}{'='*50}")
            print(f"🎯 POSITION SIZE ADJUSTER")
            print(f"{'='*50}{Style.RESET_ALL}")
            
            self.display_current_settings()
            
            print(f"\n{Fore.YELLOW}OPTIONS:{Style.RESET_ALL}")
            print("1. Quick Presets")
            print("2. Custom Values")
            print("3. Verify Bot Configuration")
            print("0. Exit")
            
            choice = input(f"\n{Fore.YELLOW}Select option: {Style.RESET_ALL}").strip()
            
            if choice == '1':
                if self.quick_presets():
                    self.save_configs()
                    input(f"\n{Fore.GREEN}Press Enter to continue...{Style.RESET_ALL}")
            elif choice == '2':
                if self.update_position_sizes():
                    self.save_configs()
                    input(f"\n{Fore.GREEN}Press Enter to continue...{Style.RESET_ALL}")
            elif choice == '3':
                self.verify_bot_uses_percentages()
                input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
            elif choice == '0':
                print(f"\n{Fore.YELLOW}Exiting...{Style.RESET_ALL}")
                break

if __name__ == "__main__":
    adjuster = PositionSizeAdjuster()
    
    # If command line argument provided, do quick adjustment
    if len(sys.argv) > 1:
        try:
            default_pct = float(sys.argv[1])
            adjuster.config['min_position_size_pct'] = default_pct - 1
            adjuster.config['default_position_size_pct'] = default_pct
            adjuster.config['max_position_size_pct'] = default_pct + 1
            
            # Remove legacy settings
            if 'min_investment_per_token' in adjuster.bot_control:
                del adjuster.bot_control['min_investment_per_token']
            if 'max_investment_per_token' in adjuster.bot_control:
                del adjuster.bot_control['max_investment_per_token']
            
            adjuster.bot_control['use_percentage_sizing'] = True
            adjuster.save_configs()
            
            print(f"{Fore.GREEN}✅ Position sizes set to {default_pct-1}-{default_pct}-{default_pct+1}%{Style.RESET_ALL}")
        except:
            print(f"{Fore.RED}Usage: python adjust_positions.py [default_percentage]{Style.RESET_ALL}")
            print(f"Example: python adjust_positions.py 5")
    else:
        # Run interactive mode
        adjuster.run()
