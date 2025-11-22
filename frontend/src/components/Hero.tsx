import React from 'react';

interface HeroProps {
  onLearnMoreClick?: () => void;
}

export const Hero: React.FC<HeroProps> = ({ onLearnMoreClick }) => {
  return (
    <section className="hero-gradient text-white relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-28">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left: Text Content */}
          <div className="relative z-10">
            <h1 className="text-4xl lg:text-5xl font-bold mb-4 leading-tight">
              SOAP Note Quality Dashboard
            </h1>
            <p className="text-lg text-blue-100 mb-8 leading-relaxed">
              Hybrid deterministic + LLM evaluation, inspired by ambient AI workflows.
              Comprehensive metrics for clinical note quality assessment.
            </p>
            <div className="flex flex-wrap gap-4">
              <button className="bg-[var(--color-primary)] hover:bg-[var(--color-primary-dark)] text-white font-semibold px-6 py-3 rounded-full transition-colors duration-200">
                View Metrics
              </button>
              <button
                onClick={onLearnMoreClick}
                className="bg-white/10 hover:bg-white/20 text-white font-semibold px-6 py-3 rounded-full border border-white/20 transition-colors duration-200"
              >
                Learn More
              </button>
            </div>
          </div>

          {/* Right: Visual Element */}
          <div className="relative z-10 hidden lg:block">
            <div className="relative">
              {/* Abstract gradient blob */}
              <div className="absolute inset-0 bg-gradient-to-br from-[var(--color-primary)]/20 to-[var(--color-primary-dark)]/20 rounded-[24px] blur-3xl transform rotate-6"></div>
              {/* Card mockup */}
              <div className="relative bg-white/10 backdrop-blur-sm rounded-[24px] p-8 border border-white/20">
                <div className="space-y-4">
                  <div className="h-3 bg-white/20 rounded w-3/4"></div>
                  <div className="h-3 bg-white/30 rounded w-full"></div>
                  <div className="h-3 bg-white/20 rounded w-5/6"></div>
                  <div className="mt-6 grid grid-cols-3 gap-4">
                    <div className="bg-white/10 rounded-lg p-4">
                      <div className="h-2 bg-[var(--color-primary)] rounded mb-2"></div>
                      <div className="h-2 bg-white/20 rounded w-2/3"></div>
                    </div>
                    <div className="bg-white/10 rounded-lg p-4">
                      <div className="h-2 bg-[var(--color-primary)] rounded mb-2"></div>
                      <div className="h-2 bg-white/20 rounded w-2/3"></div>
                    </div>
                    <div className="bg-white/10 rounded-lg p-4">
                      <div className="h-2 bg-[var(--color-primary)] rounded mb-2"></div>
                      <div className="h-2 bg-white/20 rounded w-2/3"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Decorative elements */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-[var(--color-primary)]/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-[var(--color-primary-dark)]/10 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2"></div>
    </section>
  );
};

