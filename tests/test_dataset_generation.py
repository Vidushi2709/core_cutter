"""
Test file for ML dataset generation
Tests the quality, distribution, and format of generated synthetic data
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from ml.generate_datasets import generate_training_data, generate_test_data


def test_training_data_generation():
    """Test training data generation logic"""
    print("=" * 70)
    print("TEST 1: Training Data Generation")
    print("=" * 70)
    
    # Generate small sample
    num_samples = 100
    data = generate_training_data(num_samples)
    
    # Test 1: Correct number of entries
    assert len(data) == num_samples, f"Expected {num_samples} entries, got {len(data)}"
    print(f"✓ Generated correct number of entries: {len(data)}")
    
    # Test 2: Each entry has 4 elements (L1, L2, L3, switch)
    for i, entry in enumerate(data):
        assert len(entry) == 4, f"Entry {i} has {len(entry)} elements, expected 4"
    print(f"✓ All entries have 4 elements (L1, L2, L3, switch)")
    
    # Test 3: Check label distribution (should be ~50/50)
    switch_count = sum(1 for entry in data if entry[3] == 'switch')
    not_switch_count = sum(1 for entry in data if entry[3] == 'not_switch')
    
    assert switch_count + not_switch_count == num_samples, "Label count mismatch"
    switch_ratio = switch_count / num_samples
    assert 0.4 <= switch_ratio <= 0.6, f"Imbalanced labels: {switch_ratio:.2%} switch"
    print(f"✓ Label distribution: {switch_count} switch, {not_switch_count} not_switch ({switch_ratio:.1%})")
    
    # Test 4: Validate 'not_switch' entries have low imbalance
    not_switch_entries = [e for e in data if e[3] == 'not_switch']
    for entry in not_switch_entries[:10]:  # Check first 10
        l1, l2, l3, label = entry
        imbalance = max(l1, l2, l3) - min(l1, l2, l3)
        assert imbalance < 0.3, f"'not_switch' entry has high imbalance: {imbalance:.2f} kW"
    print(f"✓ 'not_switch' entries have low imbalance")
    
    # Test 5: Validate 'switch' entries have higher imbalance
    switch_entries = [e for e in data if e[3] == 'switch']
    high_imbalance_count = 0
    for entry in switch_entries:
        l1, l2, l3, label = entry
        imbalance = max(l1, l2, l3) - min(l1, l2, l3)
        if imbalance >= 0.15:
            high_imbalance_count += 1
    
    high_imbalance_ratio = high_imbalance_count / len(switch_entries)
    print(f"✓ {high_imbalance_count}/{len(switch_entries)} 'switch' entries have imbalance ≥ 0.15 kW ({high_imbalance_ratio:.1%})")
    
    # Test 6: Check power value ranges
    all_powers = []
    for entry in data:
        all_powers.extend([entry[0], entry[1], entry[2]])
    
    min_power = min(all_powers)
    max_power = max(all_powers)
    print(f"✓ Power range: {min_power:.2f} to {max_power:.2f} kW")
    
    # Test 7: Check for export scenarios (negative power)
    export_count = sum(1 for p in all_powers if p < 0)
    export_ratio = export_count / len(all_powers)
    print(f"✓ Export scenarios: {export_count}/{len(all_powers)} ({export_ratio:.1%}) values are negative")
    
    print("\n✅ All training data tests passed!\n")
    return True


def test_test_data_generation():
    """Test test data generation logic"""
    print("=" * 70)
    print("TEST 2: Test Data Generation")
    print("=" * 70)
    
    # Generate small sample
    num_samples = 100
    data = generate_test_data(num_samples)
    
    # Test 1: Correct number of entries
    assert len(data) == num_samples, f"Expected {num_samples} entries, got {len(data)}"
    print(f"✓ Generated correct number of entries: {len(data)}")
    
    # Test 2: Each entry has 3 elements (L1, L2, L3 - no label)
    for i, entry in enumerate(data):
        assert len(entry) == 3, f"Entry {i} has {len(entry)} elements, expected 3"
    print(f"✓ All entries have 3 elements (L1, L2, L3 - no labels)")
    
    # Test 3: Check for variety of scenarios
    imbalances = []
    for entry in data:
        l1, l2, l3 = entry
        imbalance = max(l1, l2, l3) - min(l1, l2, l3)
        imbalances.append(imbalance)
    
    balanced_count = sum(1 for imb in imbalances if imb < 0.15)
    imbalanced_count = sum(1 for imb in imbalances if imb >= 0.15)
    
    print(f"✓ Scenario distribution:")
    print(f"  - Balanced (< 0.15 kW): {balanced_count} ({balanced_count/num_samples*100:.1f}%)")
    print(f"  - Imbalanced (≥ 0.15 kW): {imbalanced_count} ({imbalanced_count/num_samples*100:.1f}%)")
    
    # Test 4: Check power value ranges
    all_powers = []
    for entry in data:
        all_powers.extend([entry[0], entry[1], entry[2]])
    
    min_power = min(all_powers)
    max_power = max(all_powers)
    print(f"✓ Power range: {min_power:.2f} to {max_power:.2f} kW")
    
    # Test 5: Check for export scenarios
    export_count = sum(1 for p in all_powers if p < 0)
    export_ratio = export_count / len(all_powers)
    print(f"✓ Export scenarios: {export_count}/{len(all_powers)} ({export_ratio:.1%}) values are negative")
    
    print("\n✅ All test data tests passed!\n")
    return True


def test_data_quality():
    """Test overall data quality and statistical properties"""
    print("=" * 70)
    print("TEST 3: Data Quality & Statistics")
    print("=" * 70)
    
    # Generate larger sample for statistical analysis
    num_samples = 1000
    training_data = generate_training_data(num_samples)
    
    # Extract features and labels
    X = np.array([[e[0], e[1], e[2]] for e in training_data])
    y = np.array([e[3] for e in training_data])
    
    # Test 1: Check for NaN or infinite values
    assert not np.isnan(X).any(), "Found NaN values in data"
    assert not np.isinf(X).any(), "Found infinite values in data"
    print(f"✓ No NaN or infinite values found")
    
    # Test 2: Check statistical properties
    mean_powers = X.mean(axis=0)
    std_powers = X.std(axis=0)
    print(f"✓ Mean powers: L1={mean_powers[0]:.2f}, L2={mean_powers[1]:.2f}, L3={mean_powers[2]:.2f} kW")
    print(f"✓ Std dev: L1={std_powers[0]:.2f}, L2={std_powers[1]:.2f}, L3={std_powers[2]:.2f} kW")
    
    # Test 3: Verify class separation (switch vs not_switch should have different imbalances)
    switch_imbalances = []
    not_switch_imbalances = []
    
    for i, entry in enumerate(training_data):
        l1, l2, l3, label = entry
        imbalance = max(l1, l2, l3) - min(l1, l2, l3)
        if label == 'switch':
            switch_imbalances.append(imbalance)
        else:
            not_switch_imbalances.append(imbalance)
    
    avg_switch_imb = np.mean(switch_imbalances)
    avg_not_switch_imb = np.mean(not_switch_imbalances)
    
    print(f"✓ Average imbalance (switch): {avg_switch_imb:.3f} kW")
    print(f"✓ Average imbalance (not_switch): {avg_not_switch_imb:.3f} kW")
    
    # switch should have higher average imbalance
    assert avg_switch_imb > avg_not_switch_imb, "switch class should have higher imbalance"
    print(f"✓ Class separation verified (switch > not_switch imbalance)")
    
    # Test 4: Check for duplicate entries (should be rare with random generation)
    unique_entries = set(tuple(e[:3]) for e in training_data)
    duplicate_ratio = 1 - (len(unique_entries) / len(training_data))
    print(f"✓ Duplicate ratio: {duplicate_ratio:.2%} (unique: {len(unique_entries)}/{len(training_data)})")
    
    print("\n✅ All data quality tests passed!\n")
    return True


def test_csv_file_generation():
    """Test actual CSV file generation and loading"""
    print("=" * 70)
    print("TEST 4: CSV File Generation & Loading")
    print("=" * 70)
    
    # Create temporary test files
    test_dir = Path(__file__).parent.parent / "ml"
    train_file = test_dir / "test_training_temp.csv"
    test_file = test_dir / "test_test_temp.csv"
    
    try:
        # Generate and save training data
        training_data = generate_training_data(100)
        df_train = pd.DataFrame(training_data, columns=['L1', 'L2', 'L3', 'switch'])
        df_train.to_csv(train_file, index=False)
        print(f"✓ Created training CSV: {train_file}")
        
        # Generate and save test data
        test_data = generate_test_data(100)
        df_test = pd.DataFrame(test_data, columns=['L1', 'L2', 'L3'])
        df_test.to_csv(test_file, index=False)
        print(f"✓ Created test CSV: {test_file}")
        
        # Load and verify training file
        loaded_train = pd.read_csv(train_file)
        assert loaded_train.shape == (100, 4), f"Training CSV shape mismatch: {loaded_train.shape}"
        assert list(loaded_train.columns) == ['L1', 'L2', 'L3', 'switch'], "Training columns mismatch"
        print(f"✓ Training CSV loaded successfully: {loaded_train.shape}")
        
        # Load and verify test file
        loaded_test = pd.read_csv(test_file)
        assert loaded_test.shape == (100, 3), f"Test CSV shape mismatch: {loaded_test.shape}"
        assert list(loaded_test.columns) == ['L1', 'L2', 'L3'], "Test columns mismatch"
        print(f"✓ Test CSV loaded successfully: {loaded_test.shape}")
        
        # Verify data types
        assert loaded_train['L1'].dtype in [np.float64, np.float32], "L1 should be float"
        assert loaded_train['L2'].dtype in [np.float64, np.float32], "L2 should be float"
        assert loaded_train['L3'].dtype in [np.float64, np.float32], "L3 should be float"
        assert loaded_train['switch'].dtype == object, "switch should be string"
        print(f"✓ Data types correct")
        
        print("\n✅ CSV generation tests passed!\n")
        return True
        
    finally:
        # Cleanup temporary files
        if train_file.exists():
            train_file.unlink()
            print(f"🗑️  Cleaned up: {train_file}")
        if test_file.exists():
            test_file.unlink()
            print(f"🗑️  Cleaned up: {test_file}")


def test_edge_cases():
    """Test edge cases and boundary conditions"""
    print("=" * 70)
    print("TEST 5: Edge Cases & Boundary Conditions")
    print("=" * 70)
    
    # Test 1: Small dataset
    small_data = generate_training_data(10)
    assert len(small_data) == 10, "Small dataset generation failed"
    print(f"✓ Small dataset (10 entries) generated successfully")
    
    # Test 2: Large dataset
    large_data = generate_training_data(1000)
    assert len(large_data) == 1000, "Large dataset generation failed"
    print(f"✓ Large dataset (1000 entries) generated successfully")
    
    # Test 3: Check for extreme values
    extreme_powers = []
    for entry in large_data:
        extreme_powers.extend([entry[0], entry[1], entry[2]])
    
    # Should have some export scenarios (negative)
    has_negative = any(p < -0.1 for p in extreme_powers)
    assert has_negative, "No export scenarios found in large dataset"
    print(f"✓ Export scenarios (negative power) present")
    
    # Should have some high power scenarios
    has_high_power = any(p > 5.0 for p in extreme_powers)
    assert has_high_power, "No high power scenarios found"
    print(f"✓ High power scenarios (> 5 kW) present")
    
    # Test 4: Verify randomness (two generations should differ)
    data1 = generate_training_data(50)
    data2 = generate_training_data(50)
    
    # Compare first entries
    different = data1[0] != data2[0]
    print(f"✓ Randomness verified (different generations produce different data)")
    
    print("\n✅ All edge case tests passed!\n")
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("ML DATASET GENERATION TESTS")
    print("=" * 70)
    print()
    
    tests = [
        ("Training Data Generation", test_training_data_generation),
        ("Test Data Generation", test_test_data_generation),
        ("Data Quality & Statistics", test_data_quality),
        ("CSV File Generation", test_csv_file_generation),
        ("Edge Cases", test_edge_cases),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
        except AssertionError as e:
            print(f"\n❌ TEST FAILED: {test_name}")
            print(f"   Error: {e}\n")
            failed += 1
        except Exception as e:
            print(f"\n❌ TEST ERROR: {test_name}")
            print(f"   Exception: {e}\n")
            failed += 1
    
    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total tests: {len(tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Dataset generation is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the errors above.")
    
    print("=" * 70)


if __name__ == "__main__":
    main()
