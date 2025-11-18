#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
evaluate.py - Local performance check script
Usage: python3 evaluate.py <actual_test_csv> <student_id>
"""

import sys
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, f1_score

if len(sys.argv) != 3:
    print("Usage: python3 evaluate.py <actual_test_csv> <student_id>")
    sys.exit(1)

test_csv = sys.argv[1]
student_id = sys.argv[2]

print(f"Loading true labels from: {test_csv}")
try:
    true_df = pd.read_csv(test_csv)
except FileNotFoundError:
    print(f"Error: True label file {test_csv} not found.")
    sys.exit(1)

# --- Regression Evaluation ---
try:
    pred_reg_df = pd.read_csv(f"{student_id}_regression.csv")
    
    # 确保对齐
    merged_reg = pd.merge(true_df[['trans_num', 'amt']], 
                          pred_reg_df, 
                          on='trans_num', 
                          how='inner')
    
    y_true_reg = merged_reg['amt_x']
    y_pred_reg = merged_reg['amt_y']
    
    # 计算 RMSE
    rmse = np.sqrt(mean_squared_error(y_true_reg, y_pred_reg))
    print(f"\n✅ Regression RMSE (Test): {rmse:.2f}")

except FileNotFoundError:
    print(f"\nError: Prediction file {student_id}_regression.csv not found.")
except Exception as e:
    print(f"\nError during Regression evaluation: {e}")

# --- Classification Evaluation ---
try:
    pred_cls_df = pd.read_csv(f"{student_id}_classification.csv")
    
    # 确保对齐
    merged_cls = pd.merge(true_df[['trans_num', 'is_fraud']], 
                          pred_cls_df, 
                          on='trans_num', 
                          how='inner')
    
    y_true_cls = merged_cls['is_fraud_x']
    y_pred_cls = merged_cls['is_fraud_y']
    
    # 计算 F1 Macro
    f1 = f1_score(y_true_cls, y_pred_cls, average='macro')
    print(f"✅ Classification F1 Macro (Test): {f1:.4f}")

except FileNotFoundError:
    print(f"Error: Prediction file {student_id}_classification.csv not found.")
except Exception as e:
    print(f"Error during Classification evaluation: {e}")