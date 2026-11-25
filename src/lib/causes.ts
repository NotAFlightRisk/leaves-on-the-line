/** How each cause group reads in a sentence */
export const phrases: Record<string, string> = {
  track: 'track faults',
  assets: 'signal, points and power faults',
  weather: 'weather and structures',
  autumn: 'autumn leaves',
  external: 'outside causes like vandalism, cable theft, animals and fires',
  network: 'how the network was run',
  fleet: 'faulty trains',
  traincrew: 'traincrew problems',
  stations: 'problems at stations',
  operations: "the operators' own operations",
  'op-other': 'other operator causes'
};

/** What each group covers, for the key and the method page */
export const covers: Record<string, string> = {
  track: 'Broken rails, track defects, track circuits and the like',
  assets: 'Signals, points, power supply, overhead wires and telecoms',
  weather: 'Storms, flooding, heat, snow, and bridges, tunnels and earthworks',
  autumn: 'Leaves on the line, poor railhead adhesion and autumn working',
  external: 'Vandalism, cable theft, animals, fires, level crossings and security alerts',
  network: 'Timetabling, signallers, possessions and planning',
  fleet: 'Train faults and the depots that maintain them',
  traincrew: 'Drivers and guards: shortages, late turn-ups and errors',
  stations: 'Dispatch, passenger loading and station staff',
  operations: 'Control decisions, stock and crew planning, and operating errors',
  'op-other': "Anything else the operator's responsible for"
};

export const cause = (id: string) => `var(--cause-${id})`;
