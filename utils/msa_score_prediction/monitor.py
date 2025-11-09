# utils/monitor.py
# -*- coding: utf-8 -*-
"""
Memory and Performance Monitoring Tool
"""

import time
import psutil
import torch
from typing import Dict


class MemoryMonitor:
    """CPU and GPU memory monitoring"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.has_gpu = torch.cuda.is_available()
        self.gpu_count = torch.cuda.device_count() if self.has_gpu else 0
        if self.has_gpu:
            torch.cuda.reset_peak_memory_stats()
    
    def get_system_memory(self) -> Dict[str, float]:
        """Get system total memory information"""
        vm = psutil.virtual_memory()
        return {
            'total_gb': vm.total / (1024**3),
            'available_gb': vm.available / (1024**3),
            'used_gb': vm.used / (1024**3),
            'percent': vm.percent
        }
    
    def snapshot(self) -> Dict[str, float]:
        """Get current memory snapshot (unit: GB)"""
        mem_info = self.process.memory_info()
        sys_mem = self.get_system_memory()
        
        snapshot = {
            'cpu_mem_gb': mem_info.rss / (1024**3),
            'sys_total_gb': sys_mem['total_gb'],
            'sys_used_gb': sys_mem['used_gb'],
            'sys_available_gb': sys_mem['available_gb'],
            'sys_percent': sys_mem['percent']
        }
        
        # GPU memory (all devices)
        if self.has_gpu:
            for i in range(self.gpu_count):
                snapshot.update({
                    f'gpu{i}_allocated_gb': torch.cuda.memory_allocated(i) / (1024**3),
                    f'gpu{i}_reserved_gb': torch.cuda.memory_reserved(i) / (1024**3),
                    f'gpu{i}_peak_gb': torch.cuda.max_memory_allocated(i) / (1024**3)
                })
        
        return snapshot
    
    def format_snapshot(self, snapshot: Dict[str, float], verbose: bool = False) -> str:
        """Format memory snapshot output"""
        result = f"Process: {snapshot['cpu_mem_gb']:.2f}GB"
        
        if verbose:
            result = f"Process: {snapshot['cpu_mem_gb']:.2f}GB | System: {snapshot['sys_used_gb']:.1f}/{snapshot['sys_total_gb']:.1f}GB ({snapshot['sys_percent']:.1f}%)"
        
        if self.has_gpu:
            gpu_parts = [f"GPU{i}: {snapshot[f'gpu{i}_allocated_gb']:.2f}GB (rsrv: {snapshot[f'gpu{i}_reserved_gb']:.2f}GB)" 
                        for i in range(self.gpu_count)]
            result += " | " + " | ".join(gpu_parts)
        
        return result
    
    def print_diagnostics(self):
        """Print diagnostic information"""
        sys_mem = self.get_system_memory()
        print("\n" + "="*60)
        print("  System Diagnostics")
        print("="*60)
        print(f"CPU Memory:")
        print(f"  Total:     {sys_mem['total_gb']:.2f} GB")
        print(f"  Used:      {sys_mem['used_gb']:.2f} GB ({sys_mem['percent']:.1f}%)")
        print(f"  Available: {sys_mem['available_gb']:.2f} GB")
        print(f"\nGPU Status:")
        
        if not self.has_gpu:
            print(f"  ✗ No CUDA GPUs detected")
            print(f"  ✗ Models will run on CPU (slower, more RAM usage)")
        else:
            print(f"  ✓ {self.gpu_count} GPU(s) available")
            for i in range(self.gpu_count):
                props = torch.cuda.get_device_properties(i)
                print(f"  GPU {i}: {props.name} ({props.total_memory / (1024**3):.2f} GB)")
        
        print("="*60 + "\n")
    
    def print_task_header(self, title: str, region: str, initial_snapshot: Dict[str, float]):
        """Print task header information"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        print(f"Region: {region}")
        print(f"{'='*60}\n")
        print(f"Initial Memory: {self.format_snapshot(initial_snapshot, verbose=True)}")
    
    def print_performance_summary(self, start_time: float, timings: Dict[str, float],
                                 memory_snapshots: Dict[str, Dict], stage_map: Dict[str, tuple]):
        """Print complete performance and memory statistics"""
        total_time = time.time() - start_time
        
        print(f"\n{'='*60}")
        print(f"  Pipeline completed!")
        print(f"{'='*60}\n")
        print(f"{'='*60}")
        print(f"  Performance & Memory Summary")
        print(f"{'='*60}")
        print(f"\n{'Stage':<20} {'Time (s)':<10} {'% Total':<10} {'Mem (GB)':<12} {'Delta (GB)'}")
        print(f"{'-'*72}")
        
        prev_cpu = memory_snapshots['start']['cpu_mem_gb']
        
        for name, t in timings.items():
            pct = 100 * t / total_time
            mem_key, label = stage_map[name]
            snap = memory_snapshots[mem_key]
            cpu = snap['cpu_mem_gb']
            delta = cpu - prev_cpu
            delta_str = f"+{delta:.2f}" if delta >= 0 else f"{delta:.2f}"
            print(f"{label:<20} {t:>8.3f}    {pct:>6.1f}%    {cpu:>9.2f}    {delta_str:>9}")
            prev_cpu = cpu
        
        print(f"{'-'*72}")
        print(f"{'TOTAL':<20} {total_time:>8.3f}    100.0%")
        
        # System memory overview
        final_snap = list(memory_snapshots.values())[-1]
        print(f"\n{'System Memory:':<20} {final_snap['sys_used_gb']:.1f}/{final_snap['sys_total_gb']:.1f} GB ({final_snap['sys_percent']:.1f}% used)")
        
        # GPU statistics
        if self.has_gpu:
            print(f"\n{'GPU Memory:'}")
            for i in range(self.gpu_count):
                print(f"  GPU {i}: Peak={final_snap[f'gpu{i}_peak_gb']:.2f}GB, Current={final_snap[f'gpu{i}_allocated_gb']:.2f}GB")
        
        print(f"{'='*60}\n")