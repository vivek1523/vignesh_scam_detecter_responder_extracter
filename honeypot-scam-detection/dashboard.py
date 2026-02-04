"""
Dashboard to view scam intelligence data from the database
Run this separately to view all collected scam data
"""

from flask import Flask, render_template_string, jsonify
from database import (
    get_all_sessions, get_statistics, get_conversation_history,
    get_top_scammers, init_database
)
import json

app = Flask(__name__)

# Initialize database
init_database()

# HTML Template for Dashboard
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Scam Intelligence Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
        }
        
        .header h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #666;
            font-size: 1.1em;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        }
        
        .stat-card h3 {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        
        .stat-card .value {
            color: #667eea;
            font-size: 2.5em;
            font-weight: bold;
        }
        
        .sessions-table {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow-x: auto;
        }
        
        .sessions-table h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
        }
        
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #f0f0f0;
        }
        
        tr:hover {
            background: #f8f9fa;
        }
        
        .badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }
        
        .badge-success {
            background: #d4edda;
            color: #155724;
        }
        
        .badge-danger {
            background: #f8d7da;
            color: #721c24;
        }
        
        .badge-warning {
            background: #fff3cd;
            color: #856404;
        }
        
        .intelligence-badge {
            display: inline-block;
            background: #e7f3ff;
            color: #004085;
            padding: 3px 8px;
            border-radius: 10px;
            font-size: 0.8em;
            margin: 2px;
        }
        
        .view-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9em;
            transition: background 0.3s;
        }
        
        .view-btn:hover {
            background: #5568d3;
        }
        
        .refresh-btn {
            background: #28a745;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            margin-bottom: 20px;
            transition: background 0.3s;
        }
        
        .refresh-btn:hover {
            background: #218838;
        }
        
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
            overflow-y: auto;
        }
        
        .modal-content {
            background: white;
            margin: 50px auto;
            padding: 30px;
            border-radius: 15px;
            max-width: 800px;
            max-height: 80vh;
            overflow-y: auto;
        }
        
        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        
        .close:hover {
            color: #000;
        }
        
        .conversation-msg {
            padding: 15px;
            margin: 10px 0;
            border-radius: 10px;
        }
        
        .msg-scammer {
            background: #ffe6e6;
            border-left: 4px solid #dc3545;
        }
        
        .msg-agent {
            background: #e6f3ff;
            border-left: 4px solid #007bff;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎣 Scam Intelligence Dashboard</h1>
            <p>Real-time monitoring of scam detection and intelligence extraction</p>
        </div>
        
        <button class="refresh-btn" onclick="refreshData()">🔄 Refresh Data</button>
        
        <div class="stats-grid" id="stats-grid">
            <div class="loading">Loading statistics...</div>
        </div>
        
        <div class="sessions-table">
            <h2>Recent Scam Sessions</h2>
            <div id="sessions-container">
                <div class="loading">Loading sessions...</div>
            </div>
        </div>
    </div>
    
    <!-- Modal for conversation details -->
    <div id="conversationModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <h2>Conversation Details</h2>
            <div id="modal-content"></div>
        </div>
    </div>
    
    <script>
        // Load statistics
        async function loadStatistics() {
            try {
                const response = await fetch('/api/dashboard/statistics');
                const stats = await response.json();
                
                const statsHTML = `
                    <div class="stat-card">
                        <h3>Total Sessions</h3>
                        <div class="value">${stats.total_sessions}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Scams Detected</h3>
                        <div class="value">${stats.scams_detected}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Detection Rate</h3>
                        <div class="value">${stats.detection_rate.toFixed(1)}%</div>
                    </div>
                    <div class="stat-card">
                        <h3>Total Messages</h3>
                        <div class="value">${stats.total_messages}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Intelligence Extracted</h3>
                        <div class="value">${stats.intelligence_extracted}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Avg Confidence</h3>
                        <div class="value">${(stats.average_confidence * 100).toFixed(0)}%</div>
                    </div>
                `;
                
                document.getElementById('stats-grid').innerHTML = statsHTML;
            } catch (error) {
                console.error('Error loading statistics:', error);
            }
        }
        
        // Load sessions
        async function loadSessions() {
            try {
                const response = await fetch('/api/dashboard/sessions');
                const data = await response.json();
                
                let tableHTML = `
                    <table>
                        <thead>
                            <tr>
                                <th>Session ID</th>
                                <th>Scam Type</th>
                                <th>Status</th>
                                <th>Confidence</th>
                                <th>Messages</th>
                                <th>Intelligence</th>
                                <th>Created</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                data.sessions.forEach(session => {
                    const intelligence = {
                        banks: JSON.parse(session.bank_accounts || '[]'),
                        upis: JSON.parse(session.upi_ids || '[]'),
                        links: JSON.parse(session.phishing_links || '[]'),
                        phones: JSON.parse(session.phone_numbers || '[]')
                    };
                    
                    const intelCount = intelligence.banks.length + intelligence.upis.length + 
                                      intelligence.links.length + intelligence.phones.length;
                    
                    const statusBadge = session.scam_detected ? 
                        '<span class="badge badge-danger">SCAM</span>' :
                        '<span class="badge badge-success">Clean</span>';
                    
                    const confidenceBadge = session.scam_confidence > 0.7 ?
                        '<span class="badge badge-danger">' + (session.scam_confidence * 100).toFixed(0) + '%</span>' :
                        session.scam_confidence > 0.4 ?
                        '<span class="badge badge-warning">' + (session.scam_confidence * 100).toFixed(0) + '%</span>' :
                        '<span class="badge badge-success">' + (session.scam_confidence * 100).toFixed(0) + '%</span>';
                    
                    let intelBadges = '';
                    if (intelligence.banks.length > 0) intelBadges += `<span class="intelligence-badge">💳 ${intelligence.banks.length}</span>`;
                    if (intelligence.upis.length > 0) intelBadges += `<span class="intelligence-badge">💰 ${intelligence.upis.length}</span>`;
                    if (intelligence.links.length > 0) intelBadges += `<span class="intelligence-badge">🔗 ${intelligence.links.length}</span>`;
                    if (intelligence.phones.length > 0) intelBadges += `<span class="intelligence-badge">📱 ${intelligence.phones.length}</span>`;
                    
                    const createdDate = new Date(session.created_at).toLocaleString();
                    
                    tableHTML += `
                        <tr>
                            <td><code>${session.session_id.substring(0, 12)}...</code></td>
                            <td>${session.scam_type || 'N/A'}</td>
                            <td>${statusBadge}</td>
                            <td>${confidenceBadge}</td>
                            <td>${session.messages_exchanged}</td>
                            <td>${intelBadges || 'None'}</td>
                            <td>${createdDate}</td>
                            <td><button class="view-btn" onclick="viewConversation('${session.session_id}')">View</button></td>
                        </tr>
                    `;
                });
                
                tableHTML += '</tbody></table>';
                
                document.getElementById('sessions-container').innerHTML = tableHTML;
            } catch (error) {
                console.error('Error loading sessions:', error);
                document.getElementById('sessions-container').innerHTML = '<p class="loading">Error loading sessions</p>';
            }
        }
        
        // View conversation
        async function viewConversation(sessionId) {
            try {
                const response = await fetch(`/api/dashboard/conversation/${sessionId}`);
                const data = await response.json();
                
                let html = '<h3>Session: ' + sessionId + '</h3>';
                html += '<p><strong>Messages:</strong> ' + data.messageCount + '</p>';
                html += '<hr style="margin: 20px 0;">';
                
                data.messages.forEach(msg => {
                    const className = msg.sender === 'scammer' ? 'msg-scammer' : 'msg-agent';
                    const senderLabel = msg.sender === 'scammer' ? '🚨 Scammer' : '🤖 AI Agent';
                    const time = new Date(msg.timestamp).toLocaleTimeString();
                    
                    html += `
                        <div class="conversation-msg ${className}">
                            <strong>${senderLabel}</strong> <span style="color: #999; font-size: 0.9em;">${time}</span>
                            <p style="margin-top: 8px;">${msg.text}</p>
                        </div>
                    `;
                });
                
                document.getElementById('modal-content').innerHTML = html;
                document.getElementById('conversationModal').style.display = 'block';
            } catch (error) {
                console.error('Error loading conversation:', error);
            }
        }
        
        function closeModal() {
            document.getElementById('conversationModal').style.display = 'none';
        }
        
        function refreshData() {
            loadStatistics();
            loadSessions();
        }
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('conversationModal');
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        }
        
        // Load data on page load
        window.onload = function() {
            loadStatistics();
            loadSessions();
            
            // Auto-refresh every 30 seconds
            setInterval(refreshData, 30000);
        }
    </script>
</body>
</html>
'''

@app.route('/')
def dashboard():
    """Display the main dashboard"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/dashboard/statistics')
def api_statistics():
    """API endpoint for statistics"""
    stats = get_statistics()
    return jsonify(stats)

@app.route('/api/dashboard/sessions')
def api_sessions():
    """API endpoint for sessions list"""
    limit = 50
    sessions = get_all_sessions(limit)
    return jsonify({
        "total": len(sessions),
        "sessions": sessions
    })

@app.route('/api/dashboard/conversation/<session_id>')
def api_conversation(session_id):
    """API endpoint for conversation details"""
    messages = get_conversation_history(session_id)
    return jsonify({
        "sessionId": session_id,
        "messageCount": len(messages),
        "messages": messages
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎯 Scam Intelligence Dashboard")
    print("="*60)
    print("Open your browser and go to: http://localhost:8080")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=8080, debug=True)
