import { NextResponse } from "next/server";
import { spawn } from "child_process";
import fs from "fs/promises";
import path from "path";
import os from "os";

type GenerateRequest = {
  signals: unknown;
  today?: string;
};

const PYTHON_COMMAND = process.env.PYTHON_PATH || "python3";

async function runPython(signalsPath: string, outputPath: string, today?: string) {
  const repoRoot = path.resolve(process.cwd(), "..");
  const mainPath = path.join(repoRoot, "main.py");

  const args = [mainPath, signalsPath, outputPath];
  if (today) {
    args.push("--today", today);
  }

  return new Promise<{ stdout: string; stderr: string; code: number }>((resolve, reject) => {
    const child = spawn(PYTHON_COMMAND, args, { cwd: repoRoot });
    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (data) => {
      stdout += data.toString();
    });
    child.stderr.on("data", (data) => {
      stderr += data.toString();
    });
    child.on("close", (code) => {
      resolve({ stdout, stderr, code: code ?? 1 });
    });
    child.on("error", (error) => reject(error));
  });
}

function isValidSignalList(value: unknown): value is unknown[] {
  return Array.isArray(value);
}

export async function POST(request: Request) {
  const body = (await request.json()) as GenerateRequest;
  if (!isValidSignalList(body.signals)) {
    return NextResponse.json(
      { error: "`signals` must be an array of signal objects." },
      { status: 400 }
    );
  }

  const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "curator-"));
  const signalsPath = path.join(tmpDir, "signals.json");
  const outputPath = path.join(tmpDir, "memo.md");

  await fs.writeFile(signalsPath, JSON.stringify(body.signals, null, 2), "utf-8");

  const { stdout, stderr, code } = await runPython(signalsPath, outputPath, body.today);
  if (code !== 0) {
    return NextResponse.json(
      {
        error: "Memo generation failed.",
        stderr,
        stdout,
      },
      { status: 500 }
    );
  }

  const memo = await fs.readFile(outputPath, "utf-8");
  return NextResponse.json({ memo, stdout });
}
