"use client";

interface SwirlAvatarProps {
  className?: string;
  size?: number;
}

export function SwirlAvatar({ className = "", size = 32 }: SwirlAvatarProps) {
  const uniqueId = `swirl-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className={`relative flex-shrink-0 ${className}`} style={{ width: size, height: size }}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 48 48"
        className="absolute inset-0 transition-transform duration-300 will-change-transform hover:scale-[1.05]"
      >
        <defs>
          <radialGradient id={`${uniqueId}-swirl1`} cx="50%" cy="50%" r="60%">
            <stop offset="0%" stopColor="#22d3ee" />
            <stop offset="50%" stopColor="#3b82f6" />
            <stop offset="100%" stopColor="#1d4ed8" />
          </radialGradient>

          <radialGradient id={`${uniqueId}-swirl2`} cx="50%" cy="50%" r="40%">
            <stop offset="0%" stopColor="#60a5fa" />
            <stop offset="100%" stopColor="#22d3ee" />
          </radialGradient>

          {/* Warm accent for outer ring — Claude-ish coral/orange */}
          <radialGradient id={`${uniqueId}-swirl3`} cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#f97316" />
            <stop offset="60%" stopColor="#ec4899" />
            <stop offset="100%" stopColor="#8b5cf6" />
          </radialGradient>

          <filter id={`${uniqueId}-glow`}>
            <feGaussianBlur stdDeviation="1.5" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Subtle background circle */}
        <circle cx="24" cy="24" r="23" fill="#18181b" />
        <circle cx="24" cy="24" r="23.5" fill="none" stroke="white" strokeOpacity="0.08" />

        {/* Outer Claude-accent arc — slow spin */}
        <g style={{ transformOrigin: "24px 24px", animation: "spin 12s linear infinite" }}>
          <path
            d="M24 4 C36 4, 44 14, 44 24 C44 30, 40 35, 35 38"
            fill="none"
            stroke={`url(#${uniqueId}-swirl3)`}
            strokeWidth="2.5"
            strokeLinecap="round"
            filter={`url(#${uniqueId}-glow)`}
          />
          <path
            d="M24 44 C12 44, 4 34, 4 24 C4 18, 8 13, 13 10"
            fill="none"
            stroke={`url(#${uniqueId}-swirl3)`}
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeOpacity="0.5"
          />
        </g>

        {/* Inner blue/cyan swirl — medium spin */}
        <g style={{ transformOrigin: "24px 24px", animation: "spin 8s linear infinite" }}>
          <path
            d="M24 8 C32 8, 40 16, 40 24 C40 28, 36 32, 32 32 C28 32, 24 28, 24 24 C24 20, 28 16, 32 16 C34 16, 36 18, 36 20"
            fill="none"
            stroke={`url(#${uniqueId}-swirl1)`}
            strokeWidth="3"
            strokeLinecap="round"
            filter={`url(#${uniqueId}-glow)`}
          />
        </g>

        {/* Counter-spinning arc */}
        <g style={{ transformOrigin: "24px 24px", animation: "spin 6s linear infinite reverse" }}>
          <path
            d="M24 40 C16 40, 8 32, 8 24 C8 20, 12 16, 16 16 C20 16, 24 20, 24 24 C24 28, 20 32, 16 32 C14 32, 12 30, 12 28"
            fill="none"
            stroke={`url(#${uniqueId}-swirl2)`}
            strokeWidth="2"
            strokeLinecap="round"
            filter={`url(#${uniqueId}-glow)`}
          />
        </g>

        {/* Pulsing centre dot */}
        <circle
          cx="24"
          cy="24"
          r="4"
          fill={`url(#${uniqueId}-swirl2)`}
          filter={`url(#${uniqueId}-glow)`}
          style={{ animation: "pulse 2s ease-in-out infinite" }}
        />
      </svg>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1;   r: 4; }
          50%       { opacity: 0.6; r: 3; }
        }
      `}</style>
    </div>
  );
}
