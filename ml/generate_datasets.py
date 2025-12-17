import csv
import random

def generate_training_data(num_entries=10000):
    """Generate synthetic training data with L1, L2, L3 power values and switch labels."""
    entries = []
    
    for i in range(num_entries):
        if i % 2 == 0:  # Balanced scenarios (not_switch) - imbalance < 0.15 kW
            base = random.uniform(0.3, 6.5)
            l1 = round(base + random.uniform(-0.12, 0.12), 2)
            l2 = round(base + random.uniform(-0.12, 0.12), 2)
            l3 = round(base + random.uniform(-0.12, 0.12), 2)
            switch = "not_switch"
        else:  # Imbalanced scenarios (switch) - imbalance >= 0.15 kW
            # Create significant imbalance
            scenario = random.choice(['low_high', 'medium_low_high', 'export_imbalance'])
            
            if scenario == 'low_high':
                # One phase very low, another very high
                low = round(random.uniform(0.3, 2.0), 2)
                high = round(random.uniform(3.5, 6.5), 2)
                medium = round(random.uniform(1.5, 3.5), 2)
                powers = [low, high, medium]
            elif scenario == 'medium_low_high':
                # Gradual imbalance
                low = round(random.uniform(0.5, 2.5), 2)
                medium = round(random.uniform(2.5, 4.0), 2)
                high = round(random.uniform(4.0, 6.5), 2)
                powers = [low, medium, high]
            else:  # export_imbalance
                # Export scenario with imbalance
                low = round(random.uniform(-3.5, -0.5), 2)
                high = round(random.uniform(-0.2, 1.5), 2)
                medium = round(random.uniform(-2.0, 0.5), 2)
                powers = [low, high, medium]
            
            random.shuffle(powers)
            l1, l2, l3 = powers
            switch = "switch"
        
        entries.append([l1, l2, l3, switch])
    
    return entries

def generate_test_data(num_entries=10000):
    """Generate synthetic test data with L1, L2, L3 power values (no labels)."""
    entries = []
    
    for i in range(num_entries):
        scenario = random.choice(['balanced', 'light_imbalance', 'moderate_imbalance', 
                                 'critical_imbalance', 'export_balanced', 'export_imbalance'])
        
        if scenario == 'balanced':
            base = random.uniform(0.5, 6.0)
            l1 = round(base + random.uniform(-0.12, 0.12), 2)
            l2 = round(base + random.uniform(-0.12, 0.12), 2)
            l3 = round(base + random.uniform(-0.12, 0.12), 2)
        elif scenario == 'light_imbalance':
            base = random.uniform(1.5, 4.0)
            l1 = round(base + random.uniform(-0.2, 0.2), 2)
            l2 = round(base + random.uniform(-0.3, 0.3), 2)
            l3 = round(base + random.uniform(-0.25, 0.25), 2)
        elif scenario == 'moderate_imbalance':
            low = round(random.uniform(1.0, 2.5), 2)
            high = round(random.uniform(3.5, 5.5), 2)
            medium = round(random.uniform(2.0, 3.5), 2)
            powers = [low, high, medium]
            random.shuffle(powers)
            l1, l2, l3 = powers
        elif scenario == 'critical_imbalance':
            low = round(random.uniform(0.3, 1.5), 2)
            high = round(random.uniform(4.5, 6.8), 2)
            medium = round(random.uniform(1.5, 3.0), 2)
            powers = [low, high, medium]
            random.shuffle(powers)
            l1, l2, l3 = powers
        elif scenario == 'export_balanced':
            base = round(random.uniform(-3.0, -0.5), 2)
            l1 = round(base + random.uniform(-0.1, 0.1), 2)
            l2 = round(base + random.uniform(-0.1, 0.1), 2)
            l3 = round(base + random.uniform(-0.1, 0.1), 2)
        else:  # export_imbalance
            low = round(random.uniform(-4.0, -1.5), 2)
            high = round(random.uniform(-0.5, 1.0), 2)
            medium = round(random.uniform(-2.5, -0.5), 2)
            powers = [low, high, medium]
            random.shuffle(powers)
            l1, l2, l3 = powers
        
        entries.append([l1, l2, l3])
    
    return entries

def main():
    print("Generating synthetic phase balancing datasets...")
    
    # Generate training data
    print("\nGenerating 10000 training entries...")
    training_data = generate_training_data(10000)
    
    with open(r'c:\Users\DELL\Desktop\core_cutter\ml\phase_balancing_training_data.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(training_data)
    
    print(f"✓ Added {len(training_data)} entries to training data")
    
    # Generate test data
    print("\nGenerating 10000 test entries...")
    test_data = generate_test_data(10000)
    
    with open(r'c:\Users\DELL\Desktop\core_cutter\ml\phase_balancing_test_data.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(test_data)
    
    print(f"✓ Added {len(test_data)} entries to test data")
    
    # Verify and show statistics
    print("\n" + "="*60)
    print("DATASET STATISTICS")
    print("="*60)
    
    switch_count = sum(1 for entry in training_data if entry[3] == 'switch')
    not_switch_count = len(training_data) - switch_count
    
    print(f"\nNew Training Data:")
    print(f"  Entries added: {len(training_data)}")
    print(f"  Switch: {switch_count} ({switch_count/len(training_data)*100:.1f}%)")
    print(f"  Not Switch: {not_switch_count} ({not_switch_count/len(training_data)*100:.1f}%)")
    
    print(f"\nNew Test Data:")
    print(f"  Entries added: {len(test_data)}")
    
    # Get total line counts
    with open(r'c:\Users\DELL\Desktop\core_cutter\ml\phase_balancing_training_data.csv', 'r') as f:
        total_train = len(f.readlines()) - 1  # Exclude header
    with open(r'c:\Users\DELL\Desktop\core_cutter\ml\phase_balancing_test_data.csv', 'r') as f:
        total_test = len(f.readlines()) - 1  # Exclude header
    
    print(f"\nTotal Dataset Size:")
    print(f"  Training entries: {total_train}")
    print(f"  Test entries: {total_test}")
    
    # Sample entries
    print("\n" + "="*60)
    print("SAMPLE ENTRIES")
    print("="*60)
    print("\nTraining Data (first 5):")
    for i, entry in enumerate(training_data[:5], 1):
        l1, l2, l3, switch = entry
        imbalance = max(l1, l2, l3) - min(l1, l2, l3)
        print(f"  {i}. L1={l1}, L2={l2}, L3={l3} → {switch} (imbalance={imbalance:.2f})")
    
    print("\nTest Data (first 5):")
    for i, entry in enumerate(test_data[:5], 1):
        l1, l2, l3 = entry
        imbalance = max(l1, l2, l3) - min(l1, l2, l3)
        print(f"  {i}. L1={l1}, L2={l2}, L3={l3} (imbalance={imbalance:.2f})")
    
    print("\n✓ Datasets generated successfully!")

if __name__ == "__main__":
    main()
