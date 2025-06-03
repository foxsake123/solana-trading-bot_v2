#!/usr/bin/env python3
"""
Comprehensive ML Model Assessment for Trading Bot
Analyzes training data quality, model performance, and readiness for real trading
"""

import pandas as pd
import numpy as np
import sqlite3
import json
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from datetime import datetime, timedelta
import joblib
import warnings
warnings.filterwarnings('ignore')

class MLModelAssessment:
    def __init__(self, db_path='data/db/sol_bot.db', model_path='data/models/ml_model.pkl'):
        self.db_path = db_path
        self.model_path = model_path
        self.conn = sqlite3.connect(db_path)
        
    def load_training_data(self):
        """Load and prepare training data from database"""
        print("Loading training data from database...")
        
        # Get completed trades with outcomes
        query = """
        SELECT 
            t.*,
            tk.volume_24h,
            tk.liquidity_usd,
            tk.holders,
            tk.safety_score,
            tk.price_usd
        FROM trades t
        LEFT JOIN tokens tk ON t.contract_address = tk.contract_address
        WHERE t.action = 'SELL' 
        AND t.gain_loss_sol IS NOT NULL
        ORDER BY t.timestamp
        """
        
        df = pd.read_sql_query(query, self.conn)
        
        print(f"Loaded {len(df)} completed trades")
        return df
    
    def analyze_data_quality(self, df):
        """Analyze the quality and distribution of training data"""
        print("\n" + "="*60)
        print("DATA QUALITY ASSESSMENT")
        print("="*60)
        
        # Basic statistics
        print(f"\nTotal Trades: {len(df)}")
        print(f"Date Range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        
        # Calculate days of data
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        days_of_data = (df['timestamp'].max() - df['timestamp'].min()).days
        print(f"Days of Data: {days_of_data}")
        print(f"Average Trades per Day: {len(df) / max(days_of_data, 1):.1f}")
        
        # Outcome distribution
        profitable = (df['gain_loss_sol'] > 0).sum()
        losses = (df['gain_loss_sol'] < 0).sum()
        win_rate = profitable / len(df) * 100
        
        print(f"\nOutcome Distribution:")
        print(f"  Profitable: {profitable} ({win_rate:.1f}%)")
        print(f"  Losses: {losses} ({100-win_rate:.1f}%)")
        
        # Performance metrics
        print(f"\nPerformance Metrics:")
        print(f"  Average Gain: {df[df['gain_loss_sol'] > 0]['percentage_change'].mean():.1f}%")
        print(f"  Average Loss: {df[df['gain_loss_sol'] < 0]['percentage_change'].mean():.1f}%")
        print(f"  Best Trade: {df['percentage_change'].max():.1f}%")
        print(f"  Worst Trade: {df['percentage_change'].min():.1f}%")
        
        # Feature completeness
        print(f"\nFeature Completeness:")
        for col in ['volume_24h', 'liquidity_usd', 'holders', 'safety_score']:
            if col in df.columns:
                missing = df[col].isna().sum()
                print(f"  {col}: {100 - (missing/len(df)*100):.1f}% complete")
        
        # Market diversity
        unique_tokens = df['contract_address'].nunique()
        print(f"\nMarket Diversity:")
        print(f"  Unique Tokens Traded: {unique_tokens}")
        print(f"  Average Trades per Token: {len(df) / unique_tokens:.1f}")
        
        # Time distribution
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        print(f"\nTemporal Coverage:")
        print(f"  Hours Covered: {df['hour'].nunique()}/24")
        print(f"  Days of Week: {df['day_of_week'].nunique()}/7")
        
        return {
            'total_trades': len(df),
            'win_rate': win_rate,
            'days_of_data': days_of_data,
            'unique_tokens': unique_tokens,
            'data_quality_score': self._calculate_data_quality_score(df, days_of_data, unique_tokens)
        }
    
    def _calculate_data_quality_score(self, df, days_of_data, unique_tokens):
        """Calculate overall data quality score (0-100)"""
        score = 0
        
        # Volume of data (30 points)
        if len(df) >= 1000:
            score += 30
        elif len(df) >= 500:
            score += 20
        elif len(df) >= 200:
            score += 10
        elif len(df) >= 100:
            score += 5
        
        # Time span (20 points)
        if days_of_data >= 30:
            score += 20
        elif days_of_data >= 14:
            score += 15
        elif days_of_data >= 7:
            score += 10
        elif days_of_data >= 3:
            score += 5
        
        # Market diversity (20 points)
        if unique_tokens >= 50:
            score += 20
        elif unique_tokens >= 20:
            score += 15
        elif unique_tokens >= 10:
            score += 10
        elif unique_tokens >= 5:
            score += 5
        
        # Feature completeness (20 points)
        feature_cols = ['volume_24h', 'liquidity_usd', 'holders', 'safety_score']
        available_features = [col for col in feature_cols if col in df.columns]
        if available_features:
            completeness = sum(df[col].notna().sum() / len(df) for col in available_features) / len(available_features)
            score += int(completeness * 20)
        
        # Outcome balance (10 points)
        win_rate = (df['gain_loss_sol'] > 0).sum() / len(df)
        balance_score = 1 - abs(0.5 - win_rate) * 2  # Best at 50/50, worst at 0/100 or 100/0
        score += int(balance_score * 10)
        
        return score
    
    def evaluate_model_performance(self, df):
        """Evaluate the ML model's performance with various metrics"""
        print("\n" + "="*60)
        print("MODEL PERFORMANCE EVALUATION")
        print("="*60)
        
        # Prepare features and labels
        features = self._prepare_features(df)
        labels = (df['gain_loss_sol'] > 0).astype(int)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            features, labels, test_size=0.2, random_state=42, stratify=labels
        )
        
        # Train new model for evaluation
        model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
        model.fit(X_train, y_train)
        
        # Predictions
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        # Performance metrics
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, target_names=['Loss', 'Profit']))
        
        # ROC-AUC Score
        auc_score = roc_auc_score(y_test, y_pred_proba)
        print(f"ROC-AUC Score: {auc_score:.3f}")
        
        # Cross-validation
        cv_scores = cross_val_score(model, features, labels, cv=5, scoring='accuracy')
        print(f"\nCross-Validation Scores: {cv_scores}")
        print(f"Average CV Score: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
        
        # Feature importance
        feature_names = features.columns.tolist()
        importances = model.feature_importances_
        feature_importance = pd.DataFrame({
            'feature': feature_names,
            'importance': importances
        }).sort_values('importance', ascending=False)
        
        print("\nTop 5 Most Important Features:")
        for idx, row in feature_importance.head().iterrows():
            print(f"  {row['feature']}: {row['importance']:.3f}")
        
        return {
            'test_accuracy': model.score(X_test, y_test),
            'auc_score': auc_score,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'feature_importance': feature_importance
        }
    
    def _prepare_features(self, df):
        """Prepare features for ML model"""
        features = pd.DataFrame()
        
        # Basic features
        features['amount'] = df['amount']
        features['percentage_change'] = df['percentage_change'].fillna(0)
        
        # Time features
        features['hour'] = pd.to_datetime(df['timestamp']).dt.hour
        features['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
        
        # Token features if available
        if 'volume_24h' in df.columns:
            features['volume_24h'] = df['volume_24h'].fillna(df['volume_24h'].median())
        if 'liquidity_usd' in df.columns:
            features['liquidity_usd'] = df['liquidity_usd'].fillna(df['liquidity_usd'].median())
        if 'holders' in df.columns:
            features['holders'] = df['holders'].fillna(df['holders'].median())
        if 'safety_score' in df.columns:
            features['safety_score'] = df['safety_score'].fillna(50)
        
        return features.fillna(0)
    
    def analyze_model_stability(self, df):
        """Analyze model stability over time"""
        print("\n" + "="*60)
        print("MODEL STABILITY ANALYSIS")
        print("="*60)
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        features = self._prepare_features(df)
        labels = (df['gain_loss_sol'] > 0).astype(int)
        
        # Time-based validation
        train_size = int(len(df) * 0.8)
        X_train, X_test = features[:train_size], features[train_size:]
        y_train, y_test = labels[:train_size], labels[train_size:]
        
        # Train on historical data
        model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
        model.fit(X_train, y_train)
        
        # Test on recent data
        recent_accuracy = model.score(X_test, y_test)
        print(f"\nAccuracy on Recent Data (last 20%): {recent_accuracy:.3f}")
        
        # Rolling window validation
        window_size = min(100, len(df) // 5)
        accuracies = []
        
        for i in range(window_size, len(df), 50):
            if i + 50 > len(df):
                break
            
            # Train on data up to this point
            X_train_window = features[:i]
            y_train_window = labels[:i]
            X_test_window = features[i:i+50]
            y_test_window = labels[i:i+50]
            
            if len(np.unique(y_train_window)) < 2 or len(np.unique(y_test_window)) < 2:
                continue
            
            model_window = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
            model_window.fit(X_train_window, y_train_window)
            acc = model_window.score(X_test_window, y_test_window)
            accuracies.append(acc)
        
        if accuracies:
            print(f"\nRolling Window Performance:")
            print(f"  Average Accuracy: {np.mean(accuracies):.3f}")
            print(f"  Std Deviation: {np.std(accuracies):.3f}")
            print(f"  Min Accuracy: {np.min(accuracies):.3f}")
            print(f"  Max Accuracy: {np.max(accuracies):.3f}")
            
            # Check for performance degradation
            recent_avg = np.mean(accuracies[-3:]) if len(accuracies) >= 3 else np.mean(accuracies)
            overall_avg = np.mean(accuracies)
            
            if recent_avg < overall_avg * 0.9:
                print(f"\n⚠️  Warning: Recent performance ({recent_avg:.3f}) is below average!")
            else:
                print(f"\n✅ Model performance is stable")
        
        return {
            'recent_accuracy': recent_accuracy,
            'stability_score': self._calculate_stability_score(accuracies) if accuracies else 0
        }
    
    def _calculate_stability_score(self, accuracies):
        """Calculate model stability score (0-100)"""
        if not accuracies:
            return 0
        
        avg_acc = np.mean(accuracies)
        std_acc = np.std(accuracies)
        
        # Base score from average accuracy
        score = avg_acc * 50
        
        # Penalty for high variance
        variance_penalty = min(std_acc * 100, 25)
        score += (25 - variance_penalty)
        
        # Bonus for consistency
        if std_acc < 0.05:
            score += 25
        elif std_acc < 0.1:
            score += 15
        elif std_acc < 0.15:
            score += 5
        
        return min(score, 100)
    
    def generate_readiness_report(self):
        """Generate comprehensive readiness report for real trading"""
        print("\n" + "="*80)
        print("ML MODEL READINESS ASSESSMENT FOR REAL TRADING")
        print("="*80)
        
        # Load data
        df = self.load_training_data()
        
        # Run assessments
        data_quality = self.analyze_data_quality(df)
        model_performance = self.evaluate_model_performance(df)
        model_stability = self.analyze_model_stability(df)
        
        # Calculate overall readiness score
        readiness_score = self._calculate_readiness_score(data_quality, model_performance, model_stability)
        
        print("\n" + "="*60)
        print("READINESS SUMMARY")
        print("="*60)
        
        print(f"\nOverall Readiness Score: {readiness_score}/100")
        
        # Detailed scores
        print(f"\nComponent Scores:")
        print(f"  Data Quality: {data_quality['data_quality_score']}/100")
        print(f"  Model Performance: {int(model_performance['auc_score'] * 100)}/100")
        print(f"  Model Stability: {int(model_stability['stability_score'])}/100")
        
        # Recommendations
        print("\n" + "="*60)
        print("RECOMMENDATIONS")
        print("="*60)
        
        if readiness_score >= 80:
            print("\n✅ MODEL IS READY FOR REAL TRADING!")
            print("\nRecommended approach:")
            print("1. Start with small positions (1-2% of balance)")
            print("2. Use ML confidence threshold of 0.75 or higher")
            print("3. Monitor performance closely for first 50 trades")
            print("4. Keep simulation running in parallel for comparison")
        
        elif readiness_score >= 60:
            print("\n⚠️  MODEL IS ALMOST READY")
            print("\nNeeded improvements:")
            
            if data_quality['total_trades'] < 500:
                print("• Collect more trading data (aim for 500+ trades)")
            if data_quality['days_of_data'] < 14:
                print("• Gather data over a longer time period (14+ days)")
            if data_quality['unique_tokens'] < 20:
                print("• Trade more diverse tokens (20+ different tokens)")
            if model_performance['cv_mean'] < 0.7:
                print("• Improve model accuracy (cross-validation > 70%)")
            if model_stability['stability_score'] < 70:
                print("• Improve model stability over time")
            
            print("\nContinue in simulation for 1-2 more weeks")
        
        else:
            print("\n❌ MODEL NEEDS MORE DEVELOPMENT")
            print("\nCritical improvements needed:")
            print("• Collect at least 200-300 more trades")
            print("• Ensure data covers at least 7 days")
            print("• Improve feature engineering")
            print("• Consider different ML algorithms")
            print("\nContinue in simulation for 2-4 more weeks")
        
        # Risk considerations
        print("\n" + "="*60)
        print("RISK CONSIDERATIONS FOR REAL TRADING")
        print("="*60)
        
        print("\n1. Start Small:")
        print("   • Begin with 10% of intended capital")
        print("   • Use 1-2% position sizes initially")
        print("   • Scale up gradually based on performance")
        
        print("\n2. Safety Measures:")
        print("   • Set daily loss limit (e.g., 5% of capital)")
        print("   • Use higher ML confidence threshold initially (0.8+)")
        print("   • Manually review first 10-20 trades")
        
        print("\n3. Continuous Monitoring:")
        print("   • Compare real vs simulation performance")
        print("   • Retrain model weekly with new data")
        print("   • Track slippage and execution quality")
        
        return {
            'readiness_score': readiness_score,
            'data_quality_score': data_quality['data_quality_score'],
            'model_performance_score': int(model_performance['auc_score'] * 100),
            'model_stability_score': int(model_stability['stability_score']),
            'total_trades': data_quality['total_trades'],
            'win_rate': data_quality['win_rate'],
            'ready_for_real': readiness_score >= 80
        }
    
    def _calculate_readiness_score(self, data_quality, model_performance, model_stability):
        """Calculate overall readiness score"""
        # Weighted average of component scores
        data_weight = 0.3
        performance_weight = 0.4
        stability_weight = 0.3
        
        score = (
            data_quality['data_quality_score'] * data_weight +
            model_performance['auc_score'] * 100 * performance_weight +
            model_stability['stability_score'] * stability_weight
        )
        
        # Additional requirements
        if data_quality['total_trades'] < 100:
            score *= 0.5  # Heavy penalty for too little data
        elif data_quality['total_trades'] < 200:
            score *= 0.8
        
        if model_performance['cv_mean'] < 0.6:
            score *= 0.7  # Penalty for poor performance
        
        return int(score)

def main():
    """Run ML assessment"""
    assessor = MLModelAssessment()
    report = assessor.generate_readiness_report()
    
    # Save report
    with open('ml_readiness_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n\nReport saved to ml_readiness_report.json")
    
    return report

if __name__ == "__main__":
    main()
