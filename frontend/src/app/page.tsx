'use client';

import Link from 'next/link';
import { ArrowRight, Activity, Github, BarChart3, Brain, Zap, Users, TrendingUp } from 'lucide-react';
import dynamic from 'next/dynamic';

const Aurora = dynamic(() => import('@/components/Aurora'), { ssr: false });

export default function HomePage() {
  return (
    <div className="min-h-screen bg-neutral-950">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-neutral-950/90 backdrop-blur-sm border-b border-neutral-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-white" />
              <span className="text-base font-semibold text-white">VALORA</span>
            </div>
            
            <div className="hidden md:flex items-center gap-6">
              <Link href="/dashboard" className="text-neutral-400 hover:text-white transition-colors text-sm">
                Dashboard
              </Link>
              <Link href="/docs" className="text-neutral-400 hover:text-white transition-colors text-sm">
                Docs
              </Link>
              <Link 
                href="https://github.com" 
                target="_blank"
                className="text-neutral-400 hover:text-white transition-colors text-sm flex items-center gap-1.5"
              >
                <Github className="w-4 h-4" />
                GitHub
              </Link>
              <Link 
                href="/dashboard" 
                className="bg-white text-neutral-900 px-4 py-1.5 rounded-md text-sm font-medium hover:bg-neutral-200 transition-colors"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        {/* Aurora Background */}
        <div className="absolute inset-0">
          <Aurora 
            colorStops={["#1e3a5f", "#3d5a80", "#293241"]}
            blend={1.0}
            amplitude={0.8}
            speed={1.2}
          />
        </div>
        
        {/* Simple gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-neutral-950 via-neutral-950/50 to-neutral-950/80" />
        
        {/* Hero Content */}
        <div className="relative z-10 max-w-5xl mx-auto text-center px-4 sm:px-6 lg:px-8 pt-20">
          <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold text-white mb-8 leading-tight tracking-tight">
            Economic Simulation
            <br />
            Made Simple
          </h1>
          
          <p className="text-xl md:text-2xl text-neutral-400 max-w-3xl mx-auto mb-12">
            Run AI-powered economic simulations. Test policies. Analyze outcomes. 
            All in one platform.
          </p>
          
          <div className="flex items-center justify-center gap-6">
            <Link 
              href="/dashboard" 
              className="bg-white text-neutral-900 px-8 py-3.5 rounded-lg font-semibold text-lg hover:bg-neutral-100 transition-colors inline-flex items-center gap-2"
            >
              Open Dashboard
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link 
              href="/docs" 
              className="text-neutral-300 hover:text-white transition-colors text-lg border border-neutral-600 px-8 py-3.5 rounded-lg hover:border-neutral-400"
            >
              Learn More
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-32 px-4 sm:px-6 lg:px-8 bg-neutral-950">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-20">
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-6">
              What You Can Do
            </h2>
            <p className="text-neutral-400 text-lg md:text-xl max-w-2xl mx-auto">
              Everything you need to model and understand economic systems
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <FeatureCard
              icon={Brain}
              title="Agent Simulation"
              description="Model consumers, firms, and banks with AI-driven behavior"
            />
            <FeatureCard
              icon={BarChart3}
              title="Live Analytics"
              description="Track GDP, inflation, and employment in real-time"
            />
            <FeatureCard
              icon={Zap}
              title="Policy Testing"
              description="Test monetary and fiscal policies before implementation"
            />
            <FeatureCard
              icon={Users}
              title="Behavioral Models"
              description="Agents learn and adapt using reinforcement learning"
            />
            <FeatureCard
              icon={TrendingUp}
              title="Forecasting"
              description="Predict trends with LSTM neural networks"
            />
            <FeatureCard
              icon={Activity}
              title="Real-time Updates"
              description="WebSocket-powered live data streaming"
            />
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-32 px-4 sm:px-6 lg:px-8 bg-neutral-900">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-16 text-center">
            How It Works
          </h2>
          
          <div className="grid md:grid-cols-3 gap-12">
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-neutral-800 text-white flex items-center justify-center text-xl font-bold mx-auto mb-6">
                1
              </div>
              <h3 className="text-white text-xl font-semibold mb-3">Configure</h3>
              <p className="text-neutral-400 text-base">Set up agents, conditions, and policies</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-neutral-800 text-white flex items-center justify-center text-xl font-bold mx-auto mb-6">
                2
              </div>
              <h3 className="text-white text-xl font-semibold mb-3">Simulate</h3>
              <p className="text-neutral-400 text-base">Run the simulation and watch it evolve</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-neutral-800 text-white flex items-center justify-center text-xl font-bold mx-auto mb-6">
                3
              </div>
              <h3 className="text-white text-xl font-semibold mb-3">Analyze</h3>
              <p className="text-neutral-400 text-base">Review results and export data</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-32 px-4 sm:px-6 lg:px-8 bg-neutral-950 border-t border-neutral-800">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-6">
            Ready to start?
          </h2>
          <p className="text-neutral-400 text-lg md:text-xl mb-10">
            Launch your first simulation in minutes.
          </p>
          <Link 
            href="/dashboard" 
            className="bg-white text-neutral-900 px-8 py-3.5 rounded-lg font-semibold text-lg hover:bg-neutral-100 transition-colors inline-flex items-center gap-2"
          >
            Open Dashboard
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 sm:px-6 lg:px-8 border-t border-neutral-800 bg-neutral-950">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-neutral-500" />
            <span className="text-sm text-neutral-500">VALORA</span>
          </div>
          <div className="text-neutral-600 text-sm">
            © 2025
          </div>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({ icon: Icon, title, description }: { icon: React.ElementType; title: string; description: string }) {
  return (
    <div className="p-8 rounded-xl bg-neutral-900 border border-neutral-800 hover:border-neutral-600 transition-all hover:bg-neutral-900/80">
      <Icon className="w-8 h-8 text-neutral-300 mb-5" />
      <h3 className="text-white text-xl font-semibold mb-2">{title}</h3>
      <p className="text-neutral-400 text-base leading-relaxed">{description}</p>
    </div>
  );
}
