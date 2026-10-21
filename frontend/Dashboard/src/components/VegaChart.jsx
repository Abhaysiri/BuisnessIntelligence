import React from 'react';
import { VegaEmbed } from 'react-vega';

export default function VegaChart({ spec, title, description }) {
  if (!spec || Object.keys(spec).length === 0) {
    return null;
  }

  // Ensure spec has schema, clean dimensions, and responsive fallback
  const rawSpec = spec.vega_lite_spec || spec;
  const normalizedSpec = {
    $schema: 'https://vega.github.io/schema/vega-lite/v5.json',
    width: 460,
    height: 200,
    ...rawSpec,
    width: rawSpec.width === 'container' ? 460 : (rawSpec.width || 460),
    height: rawSpec.height || 200,
  };

  return (
    <div className="my-3 p-4 bg-white border border-slate-200 rounded-xl shadow-xs w-full max-w-xl">
      {title && (
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-0.5">{title}</h4>
      )}
      {description && (
        <p className="text-xs text-slate-500 mb-2">{description}</p>
      )}
      <div className="w-full flex justify-center overflow-x-auto py-1">
        <VegaEmbed
          spec={normalizedSpec}
          options={{
            actions: false,
            renderer: 'svg'
          }}
          onError={(err) => console.warn('Vega render notice:', err)}
        />
      </div>
    </div>
  );
}
