# styles.py
import streamlit as st
import pandas as pd
import plotly.express as px
# from utils import * # Commented out for standalone testing

def apply_custom_styles():
    st.markdown("""
    <style>
        /* ==============================
           Global Variables & Reset
           ============================== */
        :root {
            --bg-dark: #0a0b0f;
            --card-bg: #111318;
            --card-border: rgba(255, 255, 255, 0.1);
            --text-primary: #ffffff;
            --text-secondary: #9ca3af;
            --accent-green: #10b981;
            --accent-purple: #7c3aed;
            --accent-pink: #ec4899;
            --accent-gradient: linear-gradient(135deg, #00ff88, #00d4aa);
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-primary);
        }

        /* Streamlit Overrides */
        .stApp { background-color: var(--bg-dark); }
        .css-1d391kg, .css-vk32pt { background-color: var(--card-bg) !important; }
        
        /* Typography */
        h1, h2, h3 { color: var(--text-primary); }
        h2 {
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: inline-block;
        }
        p { color: var(--text-secondary); margin-bottom: 0; }

        /* ==============================
           Components
           ============================== */

        /* Cards */
        .card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            margin-bottom: 24px;
            transition: transform 0.2s ease;
        }
        .card:hover { border-color: rgba(255,255,255,0.2); }
        
        /* Flex Utilities */
        .flex-row { display: flex; align-items: center; gap: 16px; }
        .flex-between { display: flex; justify-content: space-between; align-items: flex-start; }
        .flex-center { display: flex; justify-content: center; align-items: center; }
        .gap-sm { gap: 8px; }
        .gap-md { gap: 16px; }
        .gap-lg { gap: 24px; }
        
        /* Pills & Badges */
        .pill-container { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 32px; }
        .pill {
            padding: 8px 18px;
            border-radius: 20px;
            border: 1px solid var(--card-border);
            background: transparent;
            color: var(--text-secondary);
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .pill:hover { border-color: var(--accent-purple); color: var(--text-primary); }
        .pill.active { background: var(--accent-green); color: #000; border-color: var(--accent-green); font-weight: 600; }

        .badge {
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .badge-success { background-color: #10b98120; color: #10b981; border: 1px solid #10b98140; }
        .badge-warning { background-color: #f59e0b20; color: #f59e0b; border: 1px solid #f59e0b40; }
        .badge-pink { background-color: #ec489920; color: #ec4899; border: 1px solid #ec489940; }
        
        /* Icons & Buttons */
        
         /* Target the Primary Button */
    div.stButton > button[kind="primary"] {
        /* Sizing */
        width: auto !important;             /* Minimum width based on text */
        min-width: 140px;                   /* Optional: ensures it's not too small */
        padding: 10px 24px !important;
        
        /* Styling: Outline Look */
        background-color: transparent !important; 
        border: 2px solid #00ff88 !important; /* Use accent color for border */
        color: #00ff88 !important;            /* Text matches border */
        border-radius: 8px !important;
        
        /* Effects */
        box-shadow: 0 0 12px rgba(0, 255, 136, 0.2); /* The "border shadow" glow */
        font-weight: 600;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
    }

    /* Hover State */
    div.stButton > button[kind="primary"]:hover {
        /* Make it glow brighter on hover */
        box-shadow: 0 0 25px rgba(0, 255, 136, 0.6), inset 0 0 10px rgba(0, 255, 136, 0.1); 
        color: #ffffff !important;  /* Text turns white for readability */
        border-color: #00d4aa !important;
        transform: translateY(-2px);
    }

    /* Active/Click State */
    div.stButton > button[kind="primary"]:active {
        transform: translateY(0);
        box-shadow: 0 0 5px rgba(0, 255, 136, 0.4);
    }
    
    /* Focus State (removes default red outline) */
    div.stButton > button[kind="primary"]:focus {
        border-color: #00ff88 !important;
        color: #00ff88 !important;
        .icon-btn {
            background: rgba(255,255,255,0.05);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 8px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }
        .icon-btn:hover { background: rgba(255,255,255,0.1); color: #fff; }
        
        .gradient-box {
            width: 80px; height: 80px;
            border-radius: 16px;
            background: linear-gradient(135deg, #7c3aed, #ec4899);
            display: flex; align-items: center; justify-content: center;
            box-shadow: 0 8px 16px rgba(124, 58, 237, 0.2);
        }

        /* Layout Specifics */
        .header-container {
            max-width: 900px; margin: 0 auto; padding: 32px 0;
            border-bottom: 1px solid var(--card-border);
            margin-bottom: 32px;
        }
        
        .main-container { max-width: 900px; margin: 0 auto; padding-bottom: 100px; }
        
        .status-row {
            padding: 16px 0;
            border-top: 1px solid var(--card-border);
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }

        /* Floating Input Dock */
        .floating-dock {
            position: fixed;
            bottom: 32px;
            left: 50%;
            transform: translateX(-50%);
            width: 100%;
            max-width: 700px;
            background: #181b21;
            border: 1px solid var(--card-border);
            border-radius: 28px;
            padding: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
            z-index: 999;
        }
        .dock-input {
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            color: white;
            padding: 0 12px;
            font-size: 15px;
        }
        .dock-send {
            background: var(--accent-purple);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 20px;
            font-weight: 500;
            cursor: pointer;
        }
        .dock-send:hover { brightness(1.1); }

    </style>
    """, unsafe_allow_html=True)
def render_header():
    """Render the main header using CSS classes"""
    st.markdown("""
    <div class="header-container">
        <div class="flex-between">
            <div>
                <h1 style="font-size: 28px; margin: 0; font-weight: 600;">Good evening, Mark!</h1>
                <p style="margin-top: 8px; font-size: 16px;">What would you like to explore today?</p>
            </div>
            <div class="flex-row">
                <div class="icon-btn" style="position: relative;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
                    <div style="position: absolute; top: 6px; right: 6px; width: 6px; height: 6px; background: #10b981; border-radius: 50%;"></div>
                </div>
                <div style="width: 1px; height: 24px; background: rgba(255,255,255,0.1);"></div>
                <div class="icon-btn">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_main_dashboard():
    """Renders dashboard using consistent .card and utility classes"""
    st.markdown("""
    <div class="main-container">
        
        <!-- Filter Pills -->
        <div style="margin-bottom: 24px;">
            <p style="margin-bottom: 12px; font-size: 14px;">Choose your focus</p>
            <div class="pill-container">
                <span class="pill active">Summarize reports</span>
                <span class="pill">Extract key insights</span>
                <span class="pill">Compare projects</span>
                <span class="pill">Answer questions</span>
                <span class="pill">Draft documents</span>
            </div>
        </div>

        <!-- Action Card (Small) -->
        <div class="card flex-between" style="padding: 16px 24px; align-items: center;">
            <p style="color: #fff;">Ask something about your workspace or documents.</p>
            <svg class="icon-btn" style="border:none; background:none; padding:0;" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="2"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.5 7.9c1.1-2.2 3.4-3.5 5.9-3.5h.5c4.6 0 8.5 3.5 8.9 8"></path><path d="M20.5 16.1c-1.1 2.2-3.4 3.5-5.9 3.5h-.5c-4.6 0-8.5-3.5-8.9-8"></path></svg>
        </div>

        <!-- Featured Task Card -->
        <div class="card">
            <div class="flex-row" style="align-items: flex-start;">
                <div class="gradient-box">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
                </div>
                <div style="flex: 1;">
                    <p style="color: #fff; font-size: 16px; line-height: 1.5; margin-bottom: 8px;">
                        Generate a one-page summary of the product roadmap.
                    </p>
                    <div class="flex-row gap-sm" style="font-size: 13px; color: var(--text-secondary);">
                        <div style="width: 6px; height: 6px; border-radius: 50%; background-color: #f59e0b;"></div>
                        Wait a minute
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Goals Status Card -->
        <div class="card" style="padding: 28px;">
            <div class="flex-between" style="margin-bottom: 16px;">
                <span class="badge badge-pink">GOAL</span>
            </div>
            <p style="margin-bottom: 24px; font-size: 17px; line-height: 1.6; font-weight: 500; color: #fff;">
                Deliver a unified, intelligent workspace that connects all company knowledge.
            </p>
            
            <div class="status-row">
                <div style="flex: 1;">
                    <p style="color: #fff; font-weight: 500; margin-bottom: 4px;">Phase 1: Integrations</p>
                    <p style="font-size: 14px;">Connect Google Drive, Notion, Slack and Confluence.</p>
                </div>
                <span class="badge badge-success">Completed</span>
            </div>
            
            <div class="status-row" style="border-bottom: none; padding-bottom: 0;">
                <div style="flex: 1;">
                    <p style="color: #fff; font-weight: 500; margin-bottom: 4px;">Phase 2: Contextual chat</p>
                    <p style="font-size: 14px;">Launch Ask AI interface with smart document linking.</p>
                </div>
                <span class="badge badge-success" style="background-color: #f59e0b20; color: #f59e0b; border-color: #f59e0b40;">In Progress</span>
            </div>
        </div>

        <!-- Floating Dock -->
        <div class="floating-dock">
            <button class="icon-btn" style="border:none;">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="2"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49L17.5 2.5A4 4 0 0 1 23 8l-7.1 7.1"></path></svg>
            </button>
            <button class="icon-btn" style="border:none;">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
            </button>
            <input type="text" class="dock-input" placeholder="Ask mindlink...">
            <button class="icon-btn" style="border:none;">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path></svg>
            </button>
            <button class="dock-send">Send</button>
        </div>
    </div>
    """, unsafe_allow_html=True)