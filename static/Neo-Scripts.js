// Neo-Futuristic Dashboard Interactions

document.addEventListener('DOMContentLoaded', () => {
    // Animate KPI cards on load
    const kpiCards = document.querySelectorAll('.neo-kpi-card');
    kpiCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100 * index);
    });

    // Add ripple effect to buttons
    const buttons = document.querySelectorAll('.stButton button');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const ripple = document.createElement('span');
            ripple.className = 'ripple-effect';
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 1000);
        });
    });

    // Dynamic header shadow on scroll
    const header = document.querySelector('.neo-header');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 10) {
            header.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.3)';
        } else {
            header.style.boxShadow = 'none';
        }
    });

    // Interactive tooltip for charts
    const charts = document.querySelectorAll('.plotly-graph-div');
    charts.forEach(chart => {
        chart.addEventListener('mousemove', () => {
            chart.style.transition = 'transform 0.2s';
            chart.style.transform = 'scale(1.01)';
        });
        
        chart.addEventListener('mouseleave', () => {
            chart.style.transform = 'scale(1)';
        });
    });

    // Performance monitoring
    window.addEventListener('load', () => {
        const timing = performance.timing;
        const loadTime = timing.loadEventEnd - timing.navigationStart;
        console.log(`NeoVision Dashboard loaded in ${loadTime}ms`);
        
        // Send to analytics (mock)
        setTimeout(() => {
            console.log('Performance metrics logged to analytics');
        }, 500);
    });
});

// Add global error handling
window.onerror = function(message, source, lineno, colno, error) {
    console.error('Dashboard Error:', message, error);
    return true;
};