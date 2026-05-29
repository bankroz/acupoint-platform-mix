import React from 'react';
import { CameraView } from './components/CameraView';
import { PatientPanel } from './components/PatientPanel';
import { ExpertPanel } from './components/ExpertPanel';
import { PrescriptionPanel } from './components/PrescriptionPanel';
import { SensorPanel } from './components/SensorPanel';
import { useAppStore } from './store/appStore';

const App: React.FC = () => {
  const latestResult = useAppStore((s) => s.latestResult);

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* 免责声明 */}
      <div className="disclaimer">
        当前系统为理疗辅助导航原型，不作为独立医疗诊断或自动治疗依据。
        穴位位置仅为算法推荐，需要专业人员确认。
      </div>

      {/* 主布局 */}
      <div className="flex h-[calc(100vh-32px)]">
        {/* 左侧: 摄像头 + 叠加 */}
        <div className="flex-1 p-3 flex flex-col">
          <CameraView />
          
          {/* 底部日志 */}
          <div className="mt-2 bg-gray-800 rounded p-2 text-xs text-gray-400 max-h-24 overflow-y-auto flex-1">
            <p className="text-gray-500 mb-1 font-bold">系统日志</p>
            {latestResult ? (
              <>
                <p>帧: {latestResult.acupoint_result.frame_id} | 
                   {(() => { const o = latestResult.acupoint_result.body_orientation?.orientation; const map: Record<string,string>={front:'正面',back:'背面',left_side:'左侧',right_side:'右侧',partial_front:'部分正面✅',unknown:'未知'}; return `朝向: ${map[o||''] || o || 'unknown'}`; })()} | 
                   穴位: {latestResult.acupoint_result.acupoints.filter((a: {visible: boolean}) => a.visible).length}/{latestResult.acupoint_result.acupoints.length} 可见
                   | 身体: {latestResult.pose.has_body ? '✅' : '❌'} | 手部: {latestResult.pose.has_hands ? '✅' : '❌'}
                </p>
                {latestResult.acupoint_result.acupoints.filter((a: {visible: boolean}) => a.visible).map((a: {id: string, name_cn: string, confidence: number}) => (
                  <span key={a.id} className="inline-block mr-2 px-1 bg-green-800 rounded text-green-300">{a.name_cn} {Math.round(a.confidence*100)}%</span>
                ))}
                {latestResult.acupoint_result.warnings.slice(0, 3).map((w, i) => (
                  <p key={i} className="text-yellow-500">{w}</p>
                ))}
              </>
            ) : (
              <p>等待数据...</p>
            )}
          </div>
        </div>

        {/* 右侧: 控制面板 */}
        <div className="w-80 p-3 space-y-3 overflow-y-auto">
          <PatientPanel />
          <PrescriptionPanel />
          <SensorPanel />
          <ExpertPanel />
        </div>
      </div>
    </div>
  );
};

export default App;
