import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  GitBranchPlus,
  MousePointer2,
  Play,
  Plus,
  Save,
  Trash2,
} from "lucide-react";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

const SEGMENT_KINDS = ["evaporator", "riser", "condenser", "downcomer", "connector"];
const SOLVER_MODES = ["worksheet_compatible", "distributed_steady"];
const CLOSURE_MODELS = [
  "worksheet_compatible",
  "homogeneous_equilibrium",
  "zivi",
  "regime_aware",
  "experimental_regime_aware",
];

const KIND_LABELS = {
  evaporator: "Evaporator",
  riser: "Riser",
  condenser: "Condenser",
  downcomer: "Downcomer",
  connector: "Connector",
};

const KIND_COLORS = {
  evaporator: "#c65d3a",
  riser: "#157a6e",
  condenser: "#18324a",
  downcomer: "#60758a",
  connector: "#8b6f20",
};

const fallbackScenario = {
  scenario_id: "demo-get-profile",
  name: "Demo GET profile",
  nodes: [
    { id: "n1", x_m: 0, z_m: -2 },
    { id: "n2", x_m: 200, z_m: -2 },
    { id: "n3", x_m: 200, z_m: 0.5 },
    { id: "n4", x_m: 206.5, z_m: 0.5 },
    { id: "n5", x_m: 0, z_m: -2 },
  ],
  segments: [
    { id: "s1", start_node_id: "n1", end_node_id: "n2", kind: "evaporator" },
    { id: "s2", start_node_id: "n2", end_node_id: "n3", kind: "riser" },
    { id: "s3", start_node_id: "n3", end_node_id: "n4", kind: "condenser" },
    { id: "s4", start_node_id: "n4", end_node_id: "n5", kind: "downcomer" },
  ],
  thermal: { mode: "prescribed_qtr", qtr_W_m: 76.68 },
  soil: {
    mode: "dynamic_placeholder",
    surface_z_m: 0,
    layers: [
      {
        name: "soil",
        top_z_m: 0,
        bottom_z_m: -10,
        thermal_conductivity_W_mK: 1.5,
        volumetric_heat_capacity_J_m3K: 2000000,
        latent_heat_J_m3: 80000000,
        initial_temperature_C: -1,
      },
    ],
  },
  solver: {
    tcon_C: 0,
    mode: "distributed_steady",
    closure_model: "worksheet_compatible",
    H_override_m: null,
  },
};

function App() {
  const svgRef = useRef(null);
  const [scenario, setScenario] = useState(fallbackScenario);
  const [selected, setSelected] = useState({ type: null, id: null });
  const [tool, setTool] = useState("select");
  const [pendingNodeId, setPendingNodeId] = useState(null);
  const [draggingNodeId, setDraggingNodeId] = useState(null);
  const [status, setStatus] = useState("Ready");
  const [serverResult, setServerResult] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/scenarios/demo`)
      .then((response) => (response.ok ? response.json() : Promise.reject(new Error("demo unavailable"))))
      .then((payload) => setScenario(payload.scenario))
      .catch(() => setStatus("API offline; local editing only"));
  }, []);

  const derived = useMemo(() => deriveScenario(scenario), [scenario]);
  const selectedNode = selected.type === "node" ? scenario.nodes.find((node) => node.id === selected.id) : null;
  const selectedSegment =
    selected.type === "segment" ? scenario.segments.find((segment) => segment.id === selected.id) : null;
  const viewport = useMemo(() => computeViewport(scenario.nodes), [scenario.nodes]);

  function updateScenario(mutator) {
    setScenario((current) => {
      const next = structuredClone(current);
      mutator(next);
      return next;
    });
    setServerResult(null);
  }

  function addNode() {
    updateScenario((next) => {
      const id = nextId("n", next.nodes.map((node) => node.id));
      const last = next.nodes[next.nodes.length - 1] ?? { x_m: 0, z_m: -2 };
      next.nodes.push({ id, x_m: round2(last.x_m + 10), z_m: round2(last.z_m) });
      setSelected({ type: "node", id });
    });
  }

  function deleteSelected() {
    if (!selected.id) {
      return;
    }
    updateScenario((next) => {
      if (selected.type === "node") {
        next.nodes = next.nodes.filter((node) => node.id !== selected.id);
        next.segments = next.segments.filter(
          (segment) => segment.start_node_id !== selected.id && segment.end_node_id !== selected.id,
        );
      }
      if (selected.type === "segment") {
        next.segments = next.segments.filter((segment) => segment.id !== selected.id);
      }
      setSelected({ type: null, id: null });
      setPendingNodeId(null);
    });
  }

  function handleNodePointerDown(event, nodeId) {
    event.stopPropagation();
    if (tool === "connect") {
      connectNode(nodeId);
      return;
    }
    setSelected({ type: "node", id: nodeId });
    setDraggingNodeId(nodeId);
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function handlePointerMove(event) {
    if (!draggingNodeId) {
      return;
    }
    const point = svgPoint(event);
    if (!point) {
      return;
    }
    updateScenario((next) => {
      const node = next.nodes.find((item) => item.id === draggingNodeId);
      if (node) {
        node.x_m = round2(point.x_m);
        node.z_m = round2(point.z_m);
      }
    });
  }

  function connectNode(nodeId) {
    if (!pendingNodeId) {
      setPendingNodeId(nodeId);
      setSelected({ type: "node", id: nodeId });
      return;
    }
    if (pendingNodeId === nodeId) {
      setPendingNodeId(null);
      return;
    }
    updateScenario((next) => {
      const id = nextId("s", next.segments.map((segment) => segment.id));
      next.segments.push({
        id,
        start_node_id: pendingNodeId,
        end_node_id: nodeId,
        kind: "connector",
        diameter_m: null,
        roughness_m: null,
      });
      setSelected({ type: "segment", id });
      setPendingNodeId(null);
      setTool("select");
    });
  }

  function svgPoint(event) {
    const svg = svgRef.current;
    if (!svg) {
      return null;
    }
    const point = svg.createSVGPoint();
    point.x = event.clientX;
    point.y = event.clientY;
    const matrix = svg.getScreenCTM();
    if (!matrix) {
      return null;
    }
    const transformed = point.matrixTransform(matrix.inverse());
    return { x_m: transformed.x, z_m: -transformed.y };
  }

  async function saveScenario() {
    setStatus("Saving");
    try {
      const response = await fetch(`${API_BASE}/api/scenarios`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(scenario),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail ?? "Save failed");
      }
      setStatus(`Saved ${payload.scenario.scenario_id}`);
    } catch (error) {
      setStatus(error.message);
    }
  }

  async function runScenario() {
    setStatus("Running");
    try {
      const response = await fetch(`${API_BASE}/api/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(scenario),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail ?? "Run failed");
      }
      setServerResult(payload.result);
      setStatus(payload.result.converged ? "Converged" : payload.result.solver_status ?? "Not converged");
    } catch (error) {
      setStatus(error.message);
    }
  }

  return (
    <main className="app-shell">
      <section className="topbar">
        <div>
          <h1>GET Designer</h1>
          <span>{status}</span>
        </div>
        <div className="toolbar" aria-label="Canvas tools">
          <button
            className={tool === "select" ? "active" : ""}
            onClick={() => {
              setTool("select");
              setPendingNodeId(null);
            }}
            title="Select and drag"
            aria-label="Select and drag"
          >
            <MousePointer2 size={18} />
          </button>
          <button
            className={tool === "connect" ? "active" : ""}
            onClick={() => setTool("connect")}
            title="Connect nodes"
            aria-label="Connect nodes"
          >
            <GitBranchPlus size={18} />
          </button>
          <button onClick={addNode} title="Add node" aria-label="Add node">
            <Plus size={18} />
          </button>
          <button onClick={deleteSelected} title="Delete selected" aria-label="Delete selected">
            <Trash2 size={18} />
          </button>
          <button onClick={saveScenario} title="Save scenario" aria-label="Save scenario">
            <Save size={18} />
          </button>
          <button className="run-button" onClick={runScenario} title="Run solver" aria-label="Run solver">
            <Play size={18} />
          </button>
        </div>
      </section>

      <section className="workspace">
        <aside className="panel">
          <PanelTitle title="Scenario" />
          <TextInput
            label="ID"
            value={scenario.scenario_id}
            onChange={(value) => updateScenario((next) => (next.scenario_id = value))}
          />
          <TextInput
            label="Name"
            value={scenario.name}
            onChange={(value) => updateScenario((next) => (next.name = value))}
          />
          <NumberInput
            label="qtr, W/m"
            value={scenario.thermal.qtr_W_m}
            onChange={(value) => updateScenario((next) => (next.thermal.qtr_W_m = value))}
          />
          <NumberInput
            label="tcon, C"
            value={scenario.solver.tcon_C}
            onChange={(value) => updateScenario((next) => (next.solver.tcon_C = value))}
          />
          <NumberInput
            label="H override, m"
            value={scenario.solver.H_override_m ?? ""}
            allowEmpty
            onChange={(value) => updateScenario((next) => (next.solver.H_override_m = value === "" ? null : value))}
          />
          <SelectInput
            label="Mode"
            value={scenario.solver.mode}
            options={SOLVER_MODES}
            onChange={(value) => updateScenario((next) => (next.solver.mode = value))}
          />
          <SelectInput
            label="Closure"
            value={scenario.solver.closure_model}
            options={CLOSURE_MODELS}
            onChange={(value) => updateScenario((next) => (next.solver.closure_model = value))}
          />

          <PanelTitle title="Derived" />
          <Metric label="Li" value={derived.error ? "-" : `${format(derived.evaporator_length_m)} m`} />
          <Metric label="H" value={derived.error ? "-" : `${format(derived.H_m)} m`} />
          <Metric label="Depth" value={derived.error ? "-" : `${format(derived.evaporator_depth_m)} m`} />
          <Metric label="U" value={derived.error ? "-" : `${format(derived.heat_power_W)} W`} />
          {derived.error ? <p className="error-text">{derived.error}</p> : null}
        </aside>

        <section className="canvas-panel">
          <svg
            ref={svgRef}
            className="profile-canvas"
            viewBox={`${viewport.x} ${viewport.y} ${viewport.width} ${viewport.height}`}
            onPointerMove={handlePointerMove}
            onPointerUp={() => setDraggingNodeId(null)}
            onPointerLeave={() => setDraggingNodeId(null)}
            onPointerDown={() => setSelected({ type: null, id: null })}
          >
            <Grid viewport={viewport} />
            <line
              className="ground-line"
              x1={viewport.x}
              y1={0}
              x2={viewport.x + viewport.width}
              y2={0}
            />
            {scenario.segments.map((segment) => (
              <Segment
                key={segment.id}
                segment={segment}
                nodes={scenario.nodes}
                selected={selected.type === "segment" && selected.id === segment.id}
                onSelect={(event) => {
                  event.stopPropagation();
                  setSelected({ type: "segment", id: segment.id });
                }}
              />
            ))}
            {scenario.nodes.map((node) => (
              <Node
                key={node.id}
                node={node}
                selected={selected.type === "node" && selected.id === node.id}
                pending={pendingNodeId === node.id}
                onPointerDown={(event) => handleNodePointerDown(event, node.id)}
              />
            ))}
          </svg>
        </section>

        <aside className="panel">
          <PanelTitle title="Selection" />
          {selectedNode ? (
            <>
              <TextInput label="Node ID" value={selectedNode.id} readOnly />
              <NumberInput
                label="x, m"
                value={selectedNode.x_m}
                onChange={(value) =>
                  updateScenario((next) => {
                    const node = next.nodes.find((item) => item.id === selectedNode.id);
                    if (node) node.x_m = value;
                  })
                }
              />
              <NumberInput
                label="z, m"
                value={selectedNode.z_m}
                onChange={(value) =>
                  updateScenario((next) => {
                    const node = next.nodes.find((item) => item.id === selectedNode.id);
                    if (node) node.z_m = value;
                  })
                }
              />
            </>
          ) : null}
          {selectedSegment ? (
            <>
              <TextInput label="Segment ID" value={selectedSegment.id} readOnly />
              <SelectInput
                label="Kind"
                value={selectedSegment.kind}
                options={SEGMENT_KINDS}
                onChange={(value) =>
                  updateScenario((next) => {
                    const segment = next.segments.find((item) => item.id === selectedSegment.id);
                    if (segment) segment.kind = value;
                  })
                }
              />
              <NumberInput
                label="Diameter, m"
                value={selectedSegment.diameter_m ?? ""}
                allowEmpty
                onChange={(value) =>
                  updateScenario((next) => {
                    const segment = next.segments.find((item) => item.id === selectedSegment.id);
                    if (segment) segment.diameter_m = value === "" ? null : value;
                  })
                }
              />
              <NumberInput
                label="Roughness, m"
                value={selectedSegment.roughness_m ?? ""}
                allowEmpty
                onChange={(value) =>
                  updateScenario((next) => {
                    const segment = next.segments.find((item) => item.id === selectedSegment.id);
                    if (segment) segment.roughness_m = value === "" ? null : value;
                  })
                }
              />
              <Metric label="Length" value={`${format(segmentLength(selectedSegment, scenario.nodes))} m`} />
              <Metric label="Angle" value={`${format(segmentAngle(selectedSegment, scenario.nodes))} deg`} />
            </>
          ) : null}
          {!selected.id ? <p className="muted">No selection</p> : null}

          <PanelTitle title="Result" />
          {serverResult ? (
            <>
              <Metric label="Converged" value={String(serverResult.converged)} />
              <Metric label="f" value={format(serverResult.fff)} />
              <Metric label="Hy" value={`${format(serverResult.Hy_m)} m`} />
              <Metric label="dP" value={`${format(serverResult.deltaP_Pa)} Pa`} />
              <Metric label="GL1" value={`${format(serverResult.GL1_lph)} l/h`} />
              <Metric label="Quality" value={format(serverResult.chiG1_mass)} />
            </>
          ) : (
            <p className="muted">No solver result</p>
          )}
        </aside>
      </section>
    </main>
  );
}

function Segment({ segment, nodes, selected, onSelect }) {
  const start = nodes.find((node) => node.id === segment.start_node_id);
  const end = nodes.find((node) => node.id === segment.end_node_id);
  if (!start || !end) {
    return null;
  }
  const midX = 0.5 * (start.x_m + end.x_m);
  const midY = -0.5 * (start.z_m + end.z_m);
  const length = segmentLength(segment, nodes);
  const angle = segmentAngle(segment, nodes);
  return (
    <g onPointerDown={onSelect} className={selected ? "segment selected" : "segment"}>
      <line
        x1={start.x_m}
        y1={-start.z_m}
        x2={end.x_m}
        y2={-end.z_m}
        stroke={KIND_COLORS[segment.kind] ?? KIND_COLORS.connector}
      />
      <text x={midX} y={midY - 1.6}>
        {format(length)} m / {format(angle)} deg
      </text>
    </g>
  );
}

function Node({ node, selected, pending, onPointerDown }) {
  return (
    <g className={selected ? "node selected" : pending ? "node pending" : "node"} onPointerDown={onPointerDown}>
      <circle cx={node.x_m} cy={-node.z_m} r={1.9} />
      <text x={node.x_m + 2.6} y={-node.z_m - 2.2}>
        {node.id}
      </text>
    </g>
  );
}

function Grid({ viewport }) {
  const xStart = Math.floor(viewport.x / 25) * 25;
  const xEnd = viewport.x + viewport.width;
  const yStart = Math.floor(viewport.y / 2) * 2;
  const yEnd = viewport.y + viewport.height;
  const vertical = [];
  const horizontal = [];
  for (let x = xStart; x <= xEnd; x += 25) {
    vertical.push(<line key={`x-${x}`} x1={x} y1={viewport.y} x2={x} y2={yEnd} />);
  }
  for (let y = yStart; y <= yEnd; y += 2) {
    horizontal.push(<line key={`y-${y}`} x1={viewport.x} y1={y} x2={xEnd} y2={y} />);
  }
  return <g className="grid">{vertical}{horizontal}</g>;
}

function PanelTitle({ title }) {
  return <h2>{title}</h2>;
}

function TextInput({ label, value, onChange, readOnly = false }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input value={value} readOnly={readOnly} onChange={(event) => onChange?.(event.target.value)} />
    </label>
  );
}

function NumberInput({ label, value, onChange, allowEmpty = false }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input
        type="number"
        value={value}
        onChange={(event) => {
          if (allowEmpty && event.target.value === "") {
            onChange("");
            return;
          }
          onChange(Number(event.target.value));
        }}
      />
    </label>
  );
}

function SelectInput({ label, value, options, onChange }) {
  return (
    <label className="field">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => (
          <option key={option} value={option}>
            {KIND_LABELS[option] ?? option.replaceAll("_", " ")}
          </option>
        ))}
      </select>
    </label>
  );
}

function Metric({ label, value }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value ?? "-"}</strong>
    </div>
  );
}

function deriveScenario(scenario) {
  try {
    const nodesById = new Map(scenario.nodes.map((node) => [node.id, node]));
    let totalLength = 0;
    let evaporatorLength = 0;
    let evaporatorWeightedZ = 0;
    let topZ = Math.max(...scenario.nodes.map((node) => Number(node.z_m)));
    for (const segment of scenario.segments) {
      const start = nodesById.get(segment.start_node_id);
      const end = nodesById.get(segment.end_node_id);
      if (!start || !end) {
        throw new Error(`Broken segment ${segment.id}`);
      }
      const length = distance(start, end);
      if (length <= 0) {
        throw new Error(`Zero-length segment ${segment.id}`);
      }
      totalLength += length;
      if (segment.kind === "evaporator") {
        evaporatorLength += length;
        evaporatorWeightedZ += 0.5 * (Number(start.z_m) + Number(end.z_m)) * length;
      }
    }
    if (evaporatorLength <= 0) {
      throw new Error("Add an evaporator segment");
    }
    const evaporatorMeanZ = evaporatorWeightedZ / evaporatorLength;
    const geometricHead = topZ - evaporatorMeanZ;
    const H = scenario.solver.H_override_m ?? geometricHead;
    return {
      total_length_m: totalLength,
      evaporator_length_m: evaporatorLength,
      evaporator_depth_m: -evaporatorMeanZ,
      evaporator_mean_z_m: evaporatorMeanZ,
      top_z_m: topZ,
      geometric_head_m: geometricHead,
      H_m: H,
      qtr_W_m: Number(scenario.thermal.qtr_W_m),
      heat_power_W: Number(scenario.thermal.qtr_W_m) * evaporatorLength,
      error: "",
    };
  } catch (error) {
    return { error: error.message };
  }
}

function computeViewport(nodes) {
  const xs = nodes.map((node) => Number(node.x_m));
  const zs = nodes.map((node) => Number(node.z_m));
  const minX = Math.min(...xs, 0);
  const maxX = Math.max(...xs, 10);
  const minZ = Math.min(...zs, -5);
  const maxZ = Math.max(...zs, 1);
  const marginX = Math.max(10, (maxX - minX) * 0.05);
  const marginZ = Math.max(2, (maxZ - minZ) * 0.15);
  return {
    x: minX - marginX,
    y: -maxZ - marginZ,
    width: Math.max(20, maxX - minX + 2 * marginX),
    height: Math.max(8, maxZ - minZ + 2 * marginZ),
  };
}

function segmentLength(segment, nodes) {
  const start = nodes.find((node) => node.id === segment.start_node_id);
  const end = nodes.find((node) => node.id === segment.end_node_id);
  return start && end ? distance(start, end) : 0;
}

function segmentAngle(segment, nodes) {
  const start = nodes.find((node) => node.id === segment.start_node_id);
  const end = nodes.find((node) => node.id === segment.end_node_id);
  if (!start || !end) {
    return 0;
  }
  return (Math.atan2(end.z_m - start.z_m, end.x_m - start.x_m) * 180) / Math.PI;
}

function distance(start, end) {
  return Math.hypot(Number(end.x_m) - Number(start.x_m), Number(end.z_m) - Number(start.z_m));
}

function nextId(prefix, existingIds) {
  let index = 1;
  const taken = new Set(existingIds);
  while (taken.has(`${prefix}${index}`)) {
    index += 1;
  }
  return `${prefix}${index}`;
}

function round2(value) {
  return Math.round(Number(value) * 100) / 100;
}

function format(value) {
  if (value === undefined || value === null || Number.isNaN(Number(value))) {
    return "-";
  }
  return Number(value).toLocaleString("en-US", { maximumFractionDigits: 3 });
}

createRoot(document.getElementById("root")).render(<App />);
