import React from 'react';

export default function HealthGauge({ score = 100, size = 120, strokeWidth = 10, label = 'Health Score' }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clampedScore = Math.max(0, Math.min(100, Number(score) || 0));
  const strokeDashoffset = circumference - (clampedScore / 100) * circumference;

  let strokeColor = '#10b981'; // emerald
  let glowClass = 'glow-emerald';
  if (clampedScore < 30) {
    strokeColor = '#f43f5e'; // rose
    glowClass = 'glow-rose';
  } else if (clampedScore < 50) {
    strokeColor = '#f97316'; // orange
    glowClass = 'glow-amber';
  } else if (clampedScore < 70) {
    strokeColor = '#f59e0b'; // amber
    glowClass = 'glow-amber';
  } else if (clampedScore < 85) {
    strokeColor = '#06b6d4'; // cyan
    glowClass = 'glow-cyan';
  }

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          {/* Background Track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="#1e293b"
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          {/* Animated Health Progress Arc */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={strokeColor}
            strokeWidth={strokeWidth}
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-700 ease-out"
          />
        </svg>

        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-2xl font-bold tracking-tight text-white font-mono">
            {clampedScore.toFixed(0)}
          </span>
          <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
            / 100
          </span>
        </div>
      </div>
      {label && <span className="mt-2 text-xs font-medium text-slate-400">{label}</span>}
    </div>
  );
}
