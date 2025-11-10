"""
Report generation for red teaming results.
Creates HTML and JSON reports for easy analysis.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from jinja2 import Template

from config import Config


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Red Teaming Report - {{ timestamp }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        h1 {
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 32px;
        }
        
        h2 {
            color: #34495e;
            margin-top: 30px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #ecf0f1;
        }
        
        h3 {
            color: #555;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        
        .header-info {
            color: #7f8c8d;
            margin-bottom: 30px;
            font-size: 14px;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #3498db;
        }
        
        .stat-card.critical {
            border-left-color: #e74c3c;
            background: #fee;
        }
        
        .stat-card.high {
            border-left-color: #e67e22;
            background: #fef5e7;
        }
        
        .stat-card.success {
            border-left-color: #27ae60;
        }
        
        .stat-label {
            font-size: 12px;
            text-transform: uppercase;
            color: #7f8c8d;
            margin-bottom: 5px;
        }
        
        .stat-value {
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .attack-result {
            background: #f8f9fa;
            padding: 20px;
            margin: 15px 0;
            border-radius: 6px;
            border-left: 4px solid #95a5a6;
        }
        
        .attack-result.successful {
            border-left-color: #e74c3c;
            background: #fff5f5;
        }
        
        .attack-result.critical {
            border-left-color: #c0392b;
            background: #fee;
        }
        
        .attack-meta {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            margin-bottom: 15px;
            font-size: 14px;
        }
        
        .meta-item {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .badge.critical {
            background: #e74c3c;
            color: white;
        }
        
        .badge.high {
            background: #e67e22;
            color: white;
        }
        
        .badge.medium {
            background: #f39c12;
            color: white;
        }
        
        .badge.low {
            background: #95a5a6;
            color: white;
        }
        
        .badge.none {
            background: #27ae60;
            color: white;
        }
        
        .prompt, .response {
            margin: 10px 0;
        }
        
        .section-label {
            font-weight: bold;
            color: #555;
            margin-bottom: 5px;
        }
        
        .text-box {
            background: white;
            padding: 15px;
            border-radius: 4px;
            border: 1px solid #ddd;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            white-space: pre-wrap;
            word-wrap: break-word;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .scoring-details {
            margin-top: 15px;
            padding: 15px;
            background: white;
            border-radius: 4px;
            border: 1px solid #ddd;
        }
        
        .scoring-row {
            display: grid;
            grid-template-columns: 150px 1fr;
            padding: 8px 0;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .scoring-row:last-child {
            border-bottom: none;
        }
        
        .chart-container {
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 6px;
        }
        
        .bar-chart {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .bar {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .bar-label {
            min-width: 150px;
            font-size: 14px;
        }
        
        .bar-fill {
            height: 30px;
            background: #3498db;
            border-radius: 4px;
            display: flex;
            align-items: center;
            padding: 0 10px;
            color: white;
            font-size: 12px;
            font-weight: bold;
        }
        
        .filter-buttons {
            margin: 20px 0;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        .filter-btn {
            padding: 8px 16px;
            border: 2px solid #3498db;
            background: white;
            color: #3498db;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
        }
        
        .filter-btn:hover {
            background: #3498db;
            color: white;
        }
        
        .filter-btn.active {
            background: #3498db;
            color: white;
        }
        
        footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
            text-align: center;
            color: #7f8c8d;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔴 Red Teaming Report</h1>
        <div class="header-info">
            Generated: {{ timestamp }}<br>
            Model: {{ model }}<br>
            Campaign Duration: {{ duration }} seconds
        </div>
        
        <h2>Executive Summary</h2>
        <div class="summary-grid">
            <div class="stat-card">
                <div class="stat-label">Total Attacks</div>
                <div class="stat-value">{{ summary.total_attacks }}</div>
            </div>
            <div class="stat-card {% if summary.successful_attacks > 0 %}critical{% endif %}">
                <div class="stat-label">Successful Attacks</div>
                <div class="stat-value">{{ summary.successful_attacks }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Success Rate</div>
                <div class="stat-value">{{ "%.1f"|format(summary.success_rate * 100) }}%</div>
            </div>
            <div class="stat-card {% if summary.severity_breakdown.critical > 0 %}critical{% elif summary.severity_breakdown.high > 0 %}high{% endif %}">
                <div class="stat-label">Critical Issues</div>
                <div class="stat-value">{{ summary.severity_breakdown.critical }}</div>
            </div>
        </div>
        
        <h2>Severity Distribution</h2>
        <div class="chart-container">
            <div class="bar-chart">
                {% for severity, count in summary.severity_breakdown.items() %}
                {% if count > 0 %}
                <div class="bar">
                    <div class="bar-label">{{ severity.upper() }}</div>
                    <div class="bar-fill" style="width: {{ (count / summary.total_attacks * 100) }}%; background: {% if severity == 'critical' %}#e74c3c{% elif severity == 'high' %}#e67e22{% elif severity == 'medium' %}#f39c12{% elif severity == 'low' %}#95a5a6{% else %}#27ae60{% endif %}">
                        {{ count }} ({{ "%.1f"|format(count / summary.total_attacks * 100) }}%)
                    </div>
                </div>
                {% endif %}
                {% endfor %}
            </div>
        </div>
        
        <h2>Category Performance</h2>
        <div class="chart-container">
            <div class="bar-chart">
                {% for category, rate in summary.category_success_rates.items() %}
                <div class="bar">
                    <div class="bar-label">{{ category.replace('_', ' ').title() }}</div>
                    <div class="bar-fill" style="width: {{ rate * 100 }}%;">
                        {{ "%.1f"|format(rate * 100) }}% success rate
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <h2>Detailed Results</h2>
        
        <div class="filter-buttons">
            <button class="filter-btn active" onclick="filterResults('all')">All</button>
            <button class="filter-btn" onclick="filterResults('successful')">Successful Only</button>
            <button class="filter-btn" onclick="filterResults('critical')">Critical</button>
            <button class="filter-btn" onclick="filterResults('high')">High</button>
        </div>
        
        <div id="results-container">
            {% for result in results %}
            <div class="attack-result {% if result.overall_success %}successful{% endif %} {% if result.severity == 'critical' %}critical{% endif %}" 
                 data-severity="{{ result.severity }}" 
                 data-success="{{ result.overall_success }}">
                <div class="attack-meta">
                    <div class="meta-item">
                        <strong>Strategy:</strong> {{ result.strategy_name }}
                    </div>
                    <div class="meta-item">
                        <strong>Category:</strong> {{ result.category }}
                    </div>
                    <div class="meta-item">
                        <strong>Severity:</strong> 
                        <span class="badge {{ result.severity }}">{{ result.severity }}</span>
                    </div>
                    <div class="meta-item">
                        <strong>Success:</strong> {{ "Yes" if result.overall_success else "No" }}
                    </div>
                </div>
                
                <div class="prompt">
                    <div class="section-label">Prompt:</div>
                    <div class="text-box">{{ result.prompt }}</div>
                </div>
                
                <div class="response">
                    <div class="section-label">Response:</div>
                    <div class="text-box">{{ result.response }}</div>
                </div>
                
                {% if result.overall_success %}
                <details class="scoring-details">
                    <summary style="cursor: pointer; font-weight: bold; margin-bottom: 10px;">
                        Scoring Details
                    </summary>
                    {% for scorer, scores in result.scoring_results.items() %}
                    <div class="scoring-row">
                        <strong>{{ scorer.title() }}:</strong>
                        <span>{{ scores.reasoning }} (Score: {{ "%.2f"|format(scores.score) }})</span>
                    </div>
                    {% endfor %}
                </details>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        
        <footer>
            <p><strong>⚠️ CONFIDENTIAL RED TEAMING REPORT ⚠️</strong></p>
            <p>This report contains vulnerability information. Handle with care.</p>
            <p>Generated by Atlas Red Teaming Harness</p>
        </footer>
    </div>
    
    <script>
        function filterResults(filter) {
            const results = document.querySelectorAll('.attack-result');
            const buttons = document.querySelectorAll('.filter-btn');
            
            // Update active button
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            // Filter results
            results.forEach(result => {
                const severity = result.dataset.severity;
                const success = result.dataset.success === 'true';
                
                if (filter === 'all') {
                    result.style.display = 'block';
                } else if (filter === 'successful') {
                    result.style.display = success ? 'block' : 'none';
                } else if (filter === severity) {
                    result.style.display = 'block';
                } else {
                    result.style.display = 'none';
                }
            });
        }
    </script>
</body>
</html>
"""


class ReportGenerator:
    """Generates reports from red teaming results."""
    
    def __init__(self, results_file: Path):
        """
        Initialize report generator.
        
        Args:
            results_file: Path to JSON results file
        """
        self.results_file = results_file
        with open(results_file) as f:
            self.results = json.load(f)
    
    def generate_html_report(self, output_file: Optional[Path] = None) -> Path:
        """
        Generate an HTML report.
        
        Args:
            output_file: Path to save report (auto-generated if None)
            
        Returns:
            Path to generated report
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = Config.REPORTS_DIR / f"report_{timestamp}.html"
        
        # Calculate summary statistics
        summary = self._calculate_summary()
        
        # Render template
        template = Template(HTML_TEMPLATE)
        html = template.render(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            model=Config.ATLAS_MODEL,
            duration=summary.get('duration_seconds', 0),
            summary=summary,
            results=self.results
        )
        
        # Save report
        with open(output_file, 'w') as f:
            f.write(html)
        
        return output_file
    
    def _calculate_summary(self) -> Dict[str, Any]:
        """Calculate summary statistics from results."""
        total = len(self.results)
        successful = sum(1 for r in self.results if r['overall_success'])
        
        # Severity breakdown
        severity_breakdown = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'none': 0
        }
        for result in self.results:
            severity = result['severity']
            severity_breakdown[severity] += 1
        
        # Category breakdown
        category_counts = {}
        category_success = {}
        for result in self.results:
            cat = result['category']
            category_counts[cat] = category_counts.get(cat, 0) + 1
            if result['overall_success']:
                category_success[cat] = category_success.get(cat, 0) + 1
        
        category_success_rates = {
            cat: category_success.get(cat, 0) / count
            for cat, count in category_counts.items()
        }
        
        return {
            'total_attacks': total,
            'successful_attacks': successful,
            'success_rate': successful / total if total > 0 else 0,
            'duration_seconds': 0,  # Will be set from results if available
            'severity_breakdown': severity_breakdown,
            'category_breakdown': category_counts,
            'category_success_rates': category_success_rates
        }


def generate_report_from_file(results_file: str) -> None:
    """
    Convenience function to generate report from a results file.
    
    Args:
        results_file: Path to JSON results file
    """
    generator = ReportGenerator(Path(results_file))
    report_path = generator.generate_html_report()
    print(f"Report generated: {report_path}")
    print(f"Open in browser: file://{report_path.absolute()}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python report_generator.py <results_file.json>")
        sys.exit(1)
    
    generate_report_from_file(sys.argv[1])

