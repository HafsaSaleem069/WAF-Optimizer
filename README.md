# WAF Optimizer

## Overview
WAF Optimizer is a security-focused project developed for the Information Security course. It enhances the performance and configurability of a Web Application Firewall (WAF) using ModSecurity. The goal of the project is to optimize WAF rule sets to improve efficiency while maintaining strong protection against common web vulnerabilities such as SQL injection, XSS, and CSRF attacks.

## Features
- Integration with **ModSecurity** as the WAF engine  
- Custom rule tuning for performance optimization  
- Logging and analysis of security events  
- Rule categorization based on severity and attack type  
- Automated rule testing and performance monitoring  
- Configuration dashboard for administrators (CLI or web-based)  

## Tech Stack
- **Language:** Python (scripting and automation)  
- **Tools:** ModSecurity, Apache Web Server  
- **Libraries:** Pandas, Matplotlib (for analysis and visualization)  
- **Platform:** Linux (Ubuntu)  

## Architecture
The system consists of three core modules:  
- **Rule Analyzer:** Parses ModSecurity logs and identifies inefficient or redundant rules.  
- **Optimizer Engine:** Automatically tunes rules based on detection frequency and performance metrics.  
- **Report Generator:** Produces detailed reports on security events, false positives, and performance impact.  

## Folder Structure
```
WAF-Optimizer/
│
├── src/
│   ├── analyzer.py        # Log and rule analysis
│   ├── optimizer.py       # Rule optimization logic
│   ├── reporter.py        # Report generation and visualization
│   └── main.py            # Entry point
│
├── data/
│   ├── logs/              # Sample ModSecurity logs
│   └── rules/             # Rule sets before and after optimization
│
├── docs/
│   ├── report.pdf         # Detailed report and findings
│   └── presentation.pptx  # Course presentation
│
└── README.md
```

## Security Focus Areas
- SQL Injection prevention  
- Cross-Site Scripting (XSS) detection  
- Cross-Site Request Forgery (CSRF) mitigation  
- Rate-limiting and request filtering  
- Log-based attack pattern analysis  

## Future Enhancements
- Develop a web dashboard for visual rule management  
- Add real-time alert system for attack detection  
- Implement machine learning for adaptive rule generation  

## Team Members
- Momna Shafqaat  
- [Add teammate names if applicable]  

## Course Information
- **Course:** Information Security  
- **Institution:** COMSATS University Lahore  
- **Semester:** 6th Semester  
- **Year:** 2025  

----
