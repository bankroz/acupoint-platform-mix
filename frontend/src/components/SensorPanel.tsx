import React, { useState, useEffect } from 'react';

const MOCK_SENSORS = [
  { id: 'pressure_01', type: 'pressure', name: '压力', unit: 'N', min: 0, max: 30 },
  { id: 'temp_01', type: 'temperature', name: '温度', unit: '°C', min: 20, max: 50 },
  { id: 'vib_01', type: 'vibration', name: '震动', unit: 'Hz', min: 0, max: 200 },
];

export const SensorPanel: React.FC = () => {
  const [readings, setReadings] = useState(
    MOCK_SENSORS.map((s) => ({
      ...s,
      value: (s.min + s.max) / 2,
      status: 'normal',
    }))
  );

  // 模拟传感器数据变化
  useEffect(() => {
    const interval = setInterval(() => {
      setReadings((prev) =>
        prev.map((s) => ({
          ...s,
          value: s.min + Math.random() * (s.max - s.min),
          status: Math.random() > 0.9 ? 'warning' : 'normal',
        }))
      );
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const getBarColor = (sensor: typeof readings[0]) => {
    if (sensor.status === 'warning') return 'bg-yellow-500';
    if (sensor.type === 'pressure') return 'bg-green-500';
    if (sensor.type === 'temperature') return 'bg-orange-500';
    return 'bg-blue-500';
  };

  const getPercent = (sensor: typeof readings[0]) => {
    return ((sensor.value - sensor.min) / (sensor.max - sensor.min)) * 100;
  };

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h3 className="text-white font-bold text-lg mb-3">
        传感器数据 <span className="text-gray-500 text-xs font-normal">(Mock)</span>
      </h3>
      <div className="space-y-3">
        {readings.map((sensor) => (
          <div key={sensor.id}>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-gray-400">{sensor.name}</span>
              <span className={`${sensor.status === 'warning' ? 'text-yellow-400' : 'text-gray-300'}`}>
                {sensor.value.toFixed(1)} {sensor.unit}
              </span>
            </div>
            <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${getBarColor(sensor)}`}
                style={{ width: `${Math.min(getPercent(sensor), 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
