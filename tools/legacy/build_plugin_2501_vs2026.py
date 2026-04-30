#!/usr/bin/env python3
"""
Build script for nsis7z plugin (7-Zip 25.01 version) - Visual Studio 2026
Supports multiple build configurations with flexible parameters
Uses PlatformToolset v145 (Visual Studio 2026 Build Tools)

NOTE: VS2026 Build Tools use v145 toolset (version 18.x)
"""

import argparse
import os
import sys
import subprocess
import shutil
import time
import multiprocessing
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Tuple, Optional
import xml.etree.ElementTree as ET


class BuildConfig:
    """Configuration for a single build target"""
    def __init__(self, name: str, config: str, platform: str, dest_dir: str):
        self.name = name
        self.config = config
        self.platform = platform
        self.dest_dir = dest_dir


# Predefined build configurations
CONFIGS = {
    'x86-unicode': BuildConfig(
        name='x86-unicode',
        config='Release Unicode',
        platform='Win32',
        dest_dir='x86-unicode'
    ),
    'x64-unicode': BuildConfig(
        name='x64-unicode',
        config='Release Unicode',
        platform='x64',
        dest_dir='amd64-unicode'
    ),
    'x86-ansi': BuildConfig(
        name='x86-ansi',
        config='Release',
        platform='Win32',
        dest_dir='x86-ansi'
    ),
}





# Standard vswhere.exe location (installed with any VS 2017+ setup)
_VSWHERE_PATH = Path(r'C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe')

# vswhere version range per VS year
_VS_VERSION_RANGE = {
    '2026': '[18.0,19.0)',
    '2022': '[17.0,18.0)',
}

# MSBuild toolset per VS year
_VS_TOOLSET = {
    '2026': 'v145',  # VS 2026 uses v145 toolset
    '2022': 'v143',  # VS 2022 uses v143 toolset
}


def _find_msbuild_via_vswhere(vs_version: str) -> 'Optional[Tuple[Path, str, str]]':
    """Locate MSBuild via vswhere.exe."""
    if not _VSWHERE_PATH.exists():
        return None
    versions_to_try = ['2026', '2022'] if vs_version == 'auto' else [vs_version]
    for ver in versions_to_try:
        if ver not in _VS_VERSION_RANGE:
            continue
        try:
            result = subprocess.run(
                [
                    str(_VSWHERE_PATH),
                    '-products', '*',
                    '-version', _VS_VERSION_RANGE[ver],
                    '-latest',
                    '-requires', 'Microsoft.Component.MSBuild',
                    '-find', r'MSBuild\**\Bin\MSBuild.exe',
                ],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0:
                lines = [ln.strip() for ln in result.stdout.splitlines() if ln.strip()]
                if lines:
                    msbuild_path = Path(lines[0])
                    if msbuild_path.exists():
                        return msbuild_path, _VS_TOOLSET[ver], ver
        except Exception:
            pass
    return None


# Numeric version folder used by VS2026 installer (version 18.x)
_VS_NUMERIC_FOLDER = {
    '2026': '18',
    '2022': '2022',
}


def find_msbuild(vs_version: str = 'auto') -> 'Optional[Tuple[Path, str, str]]':
    """Find MSBuild.exe via vswhere, then well-known fallback paths.

    Returns (msbuild_path, toolset_version, vs_year) or None.
    """
    result = _find_msbuild_via_vswhere(vs_version)
    if result is not None:
        return result

    vs_editions = ['Community', 'Professional', 'Enterprise', 'BuildTools']
    versions_to_try = ['2026', '2022'] if vs_version == 'auto' else [vs_version]
    for version in versions_to_try:
        numeric = _VS_NUMERIC_FOLDER.get(version, version)
        base_paths = [
            Path(rf'C:\Program Files (x86)\Microsoft Visual Studio\{numeric}'),
            Path(rf'C:\Program Files\Microsoft Visual Studio\{version}'),
        ]
        for base_path in base_paths:
            for edition in vs_editions:
                msbuild_path = base_path / edition / 'MSBuild' / 'Current' / 'Bin' / 'MSBuild.exe'
                if msbuild_path.exists():
                    return msbuild_path, _VS_TOOLSET[version], version
    return None

def get_project_paths() -> Tuple[Path, Path, Path]:
    """Get project directory, project file, and plugins directory"""
    script_dir = Path(__file__).parent.absolute()
    project_dir = script_dir.parent.parent / 'versions' / '25.01'
    project_file = project_dir / 'CPP' / '7zip' / 'Bundles' / 'Nsis7z' / 'Nsis7z_vs2026.vcxproj'
    plugins_dir = script_dir.parent.parent / 'plugins'
    
    return project_dir, project_file, plugins_dir


def get_cpu_info() -> dict:
    """Get CPU information for parallel build optimization"""
    try:
        import psutil
        logical_cores = psutil.cpu_count(logical=True)
        physical_cores = psutil.cpu_count(logical=False)
        
        return {
            'logical_cores': logical_cores,
            'physical_cores': physical_cores,
            'has_hyperthreading': logical_cores > physical_cores,
            'has_psutil': True
        }
    except ImportError:
        # Fallback if psutil is not available
        cpu_count = multiprocessing.cpu_count()
        return {
            'logical_cores': cpu_count,
            'physical_cores': cpu_count,
            'has_hyperthreading': False,
            'has_psutil': False
        }


def get_optimal_thread_count() -> int:
    """Get optimal thread count for compilation"""
    cpu_info = get_cpu_info()
    
    # Use physical cores for optimal performance (avoids hyperthreading overhead in compilation)
    if cpu_info['has_hyperthreading'] and cpu_info['physical_cores'] > 1:
        return cpu_info['physical_cores']
    else:
        return cpu_info['logical_cores']


def get_build_optimizations() -> List[str]:
    """Get additional build optimization flags"""
    return [
        '/p:BuildInParallel=true',           # Enable parallel project builds
        '/p:MultiProcessorCompilation=true', # Enable MP compilation
        '/p:PreferredToolArchitecture=x64',  # Use 64-bit tools (faster)
        '/p:UseSharedCompilation=true',      # Enable shared compilation
        '/p:TrackFileAccess=false',          # Disable file tracking (faster)
        '/nodeReuse:true',                   # Reuse MSBuild nodes
        '/p:GenerateResourceUsePreserializedResources=true'  # Faster resources
    ]


def get_memory_optimizations() -> List[str]:
    """Get memory optimization flags for faster builds"""
    try:
        import psutil
        # Get available memory in GB
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        if memory_gb >= 16:
            # High memory system - aggressive caching
            return [
                '/p:DisableFastUpToDateCheck=false',
                '/p:BuildProjectReferences=true',
                '/p:UseCommonOutputDirectory=false'
            ]
        elif memory_gb >= 8:
            # Medium memory system
            return [
                '/p:DisableFastUpToDateCheck=false'
            ]
        else:
            # Low memory system - conservative
            return []
    except ImportError:
        # Conservative defaults without psutil
        return ['/p:DisableFastUpToDateCheck=false']


def print_cpu_info(use_parallel: bool, use_optimizations: bool = True) -> None:
    """Print CPU information for build optimization"""
    if not use_parallel:
        print("Build mode:         Single-threaded")
        if use_optimizations:
            print("Optimizations:      ENABLED (memory, caching)")
        return
    
    cpu_info = get_cpu_info()
    optimal_threads = get_optimal_thread_count()
    
    print("Build mode:         Parallel")
    print(f"Logical cores:      {cpu_info['logical_cores']}")
    print(f"Physical cores:     {cpu_info['physical_cores']}")
    
    if cpu_info['has_hyperthreading']:
        print("Hyperthreading:     ENABLED")
        print(f"Optimal threads:    {optimal_threads} (using physical cores)")
    else:
        print("Hyperthreading:     NOT AVAILABLE")
        print(f"Optimal threads:    {optimal_threads}")
    
    print(f"MSBuild threads:    {optimal_threads}")
    
    if use_optimizations:
        print("Optimizations:      ENABLED (parallel, memory, caching)")
        try:
            import psutil
            memory_gb = psutil.virtual_memory().total / (1024**3)
            print(f"Available memory:   {memory_gb:.1f} GB")
        except ImportError:
            print("Available memory:   Unknown (install psutil for details)")
    else:
        print("Optimizations:      DISABLED")
    
    if not cpu_info['has_psutil']:
        print("Note: Install 'psutil' for detailed CPU/memory info (pip install psutil)")
    
    print()


def build_configuration(
    msbuild_path: Path,
    project_file: Path,
    config: BuildConfig,
    rebuild: bool = True,
    verbosity: str = 'quiet',
    parallel: bool = True,
    optimizations: bool = True,
    counter: str = "",
    capture_output: bool = False
) -> Tuple[bool, float, str]:
    """Build a single configuration
    
    Returns:
        Tuple of (success: bool, elapsed_time: float, captured_output: str)
    """
    
    # Build MSBuild command
    cmd = [
        str(msbuild_path),
        str(project_file),
        f'/t:{"Rebuild" if rebuild else "Build"}',
        f'/p:Configuration={config.config}',
        f'/p:Platform={config.platform}',
        f'/p:OutDir=Build\\{config.name}\\',
        f'/p:IntDir=Build\\{config.name}\\obj\\',
        '/p:WindowsTargetPlatformVersion=10.0',
        '/p:PlatformToolset=v145',
        f'/v:{verbosity}',
    ]
    
    if parallel:
        optimal_threads = get_optimal_thread_count()
        cmd.extend([
            f'/maxcpucount:{optimal_threads}',
            '/p:UseMultiToolTask=true',
            f'/p:CL_MPCount={optimal_threads}'
        ])
    
    # Add build optimizations
    if optimizations:
        cmd.extend(get_build_optimizations())
        cmd.extend(get_memory_optimizations())
        
        # Add cache directory if available
        cache_dir = setup_build_cache()
        if cache_dir:
            cmd.append(f'/p:MSBuildCacheEnabled=true')
    
    if not capture_output:
        print(f"\n{'='*50}")
        if counter:
            print(f"Building {config.name} [{counter}]")
        else:
            print(f"Building {config.name}...")
        print('='*50)
    
    # Execute build and measure time
    start_time = time.time()
    try:
        if capture_output:
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)
            elapsed = time.time() - start_time
            return result.returncode == 0, elapsed, result.stdout + result.stderr
        else:
            result = subprocess.run(cmd, check=False)
            elapsed = time.time() - start_time
            return result.returncode == 0, elapsed, ""
    except Exception as e:
        elapsed = time.time() - start_time
        msg = f"ERROR: Build failed with exception: {e}"
        if capture_output:
            return False, elapsed, msg
        print(msg)
        return False, elapsed, ""


def copy_output(
    project_dir: Path,
    plugins_dir: Path,
    config: BuildConfig
) -> Tuple[bool, int, Optional[Path]]:
    """Copy built DLL to destination directory

    Returns:
        Tuple of (success: bool, file_size: int, dest_path: Optional[Path])
    """
    
    # Output is in Build\{config.name}\ relative to project directory
    output_file = project_dir / 'CPP' / '7zip' / 'Bundles' / 'Nsis7z' / 'Build' / config.name / 'nsis7z.dll'
    dest_dir = plugins_dir / config.dest_dir
    
    if not output_file.exists():
        print(f"ERROR: {config.name} DLL not found at {output_file}")
        return False, 0, None
    
    # Create destination directory
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy file
    try:
        dest_path = dest_dir / 'nsis7z.dll'
        shutil.copy2(output_file, dest_path)
        file_size = output_file.stat().st_size
        print(f"SUCCESS: {config.name} - {file_size:,} bytes - Copied to {dest_dir}")
        return True, file_size, dest_path
    except Exception as e:
        print(f"ERROR: Failed to copy {config.name}: {e}")
        return False, 0, None


def clean_build_artifacts(project_dir: Path, configs: List[BuildConfig]) -> None:
    """Clean up build artifacts"""
    print("\nCleaning build artifacts...")
    
    build_base_dir = project_dir / 'CPP' / '7zip' / 'Bundles' / 'Nsis7z' / 'Build'
    
    # Collect unique output directories
    dirs_to_clean = set()
    for config in configs:
        output_dir = build_base_dir / config.name
        dirs_to_clean.add(output_dir)
    
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                print(f"  - Cleaned: {dir_path.name}")
            except Exception as e:
                print(f"  - Failed to clean {dir_path.name}: {e}")
    
    print("Build artifacts cleaned successfully.")


def format_time(seconds: float) -> str:
    """Format time in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.0f}s"


def setup_build_cache() -> Optional[str]:
    """Setup build cache directory for faster incremental builds"""
    try:
        cache_dir = Path.home() / '.msbuild_cache' / 'nsis7z-2501-vs2026'
        cache_dir.mkdir(parents=True, exist_ok=True)
        return str(cache_dir)
    except Exception:
        return None


def wait_for_key() -> bool:
    """Wait for user to press a key. Returns False if 'q' is pressed."""
    print("\nPress any key to continue, or 'q' to quit...")
    try:
        if sys.platform == 'win32':
            import msvcrt
            key = msvcrt.getch()
            return key.lower() not in (b'q', b'Q')
        else:
            import termios
            import tty
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                key = sys.stdin.read(1)
                return key.lower() not in ('q', 'Q')
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except Exception:
        input()  # Fallback to input()
        return True


def get_available_configurations(project_file: Path) -> List[Tuple[str, str]]:
    """Parse .vcxproj file to get available configurations
    
    Returns:
        List of (Configuration, Platform) tuples
    """
    try:
        tree = ET.parse(project_file)
        root = tree.getroot()
        
        # XML namespace for MSBuild project files
        ns = {'ms': 'http://schemas.microsoft.com/developer/msbuild/2003'}
        
        configs = []
        for item_group in root.findall('.//ms:ItemGroup', ns):
            for proj_config in item_group.findall('ms:ProjectConfiguration', ns):
                include = proj_config.get('Include')
                if include:
                    # Format is "Configuration|Platform"
                    parts = include.split('|')
                    if len(parts) == 2:
                        configs.append((parts[0], parts[1]))
        
        return configs
    except Exception as e:
        print(f"Warning: Could not parse project file: {e}")
        return []


def print_available_configurations(project_file: Path) -> None:
    """Print all configurations available in the project"""
    configs = get_available_configurations(project_file)
    
    if not configs:
        print("No configurations found or could not read project file.")
        return
    
    print("Available configurations in project:")
    print("-" * 60)
    
    # Group by configuration name
    from collections import defaultdict
    grouped = defaultdict(list)
    for config, platform in configs:
        grouped[config].append(platform)
    
    for config_name in sorted(grouped.keys()):
        platforms = ', '.join(sorted(grouped[config_name]))
        print(f"  {config_name:25s} - {platforms}")
    
    print(f"\nTotal: {len(configs)} configuration(s)")
    print()
    
    # Show which ones are mapped in this script
    print("Configurations mapped in this build script:")
    print("-" * 60)
    for name, config in CONFIGS.items():
        print(f"  {name:15s} -> {config.config} / {config.platform}")
    print()



_print_lock = threading.Lock()


def _build_configs_parallel(
    msbuild_path: Path,
    project_file: Path,
    configs: 'List[BuildConfig]',
    *,
    rebuild: bool,
    verbosity: str,
    parallel: bool,
    optimizations: bool,
    project_dir: Path,
    plugins_dir: Path,
) -> list:
    """Build all configurations simultaneously, printing output atomically.

    Returns list of (config, success, build_time, file_size, dest_path) tuples
    in the same order as *configs*.
    """
    n = len(configs)
    print(f"\nParallel-configs: launching {n} builds simultaneously...")
    print("=" * 50)

    total_start = time.time()
    results_by_idx: dict = {}
    idx_lock = threading.Lock()

    def _build_one(idx: int, config: 'BuildConfig'):
        success, build_time, captured = build_configuration(
            msbuild_path, project_file, config,
            rebuild=rebuild, verbosity=verbosity,
            parallel=parallel, optimizations=optimizations,
            capture_output=True,
        )
        import io
        import contextlib
        copy_buf = io.StringIO()
        if success:
            with contextlib.redirect_stdout(copy_buf):
                copy_ok, file_size, dest_path = copy_output(project_dir, plugins_dir, config)
        else:
            copy_ok, file_size, dest_path = False, 0, None

        with _print_lock:
            all_ok = success and copy_ok
            tag = "OK" if all_ok else "FAILED"
            size_str = f"{file_size:,} bytes" if file_size > 0 else "N/A"
            print(f"[{tag}] {config.name}  ({format_time(build_time)})  {size_str}")
            if dest_path:
                print(f"        -> {dest_path}")
            if not all_ok:
                copy_out = copy_buf.getvalue()
                if copy_out.strip():
                    print(copy_out.rstrip())
                if captured.strip():
                    print("--- Build output ---")
                    print(captured.rstrip())

        with idx_lock:
            results_by_idx[idx] = (config, success and copy_ok, build_time, file_size, dest_path)

    with ThreadPoolExecutor(max_workers=n) as executor:
        futures = {executor.submit(_build_one, i, cfg): i for i, cfg in enumerate(configs)}
        for fut in as_completed(futures):
            exc = fut.exception()
            if exc:
                idx = futures[fut]
                with _print_lock:
                    print(f"ERROR: worker for config index {idx} raised: {exc}")
                with idx_lock:
                    results_by_idx[idx] = (configs[idx], False, 0.0, 0, None)

    wall_time = time.time() - total_start
    print(f"\nAll {n} configs finished in {format_time(wall_time)} (wall clock)")
    return [results_by_idx[i] for i in range(n)]

def main():
    """Main build function"""
    parser = argparse.ArgumentParser(
        description='Build nsis7z plugin for NSIS (7-Zip 25.01, Visual Studio 2026)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Build all configurations
  %(prog)s --list                   # List script configurations
  %(prog)s --list-project           # List all project configurations
  %(prog)s --configs x86-unicode    # Build only x86-unicode
  %(prog)s --configs x86-unicode x64-unicode  # Build specific configs
  %(prog)s --no-rebuild             # Incremental build
  %(prog)s --no-parallel            # Single-threaded build
  %(prog)s --no-clean               # Skip cleanup
  %(prog)s --verbosity minimal      # Show more build output
  %(prog)s --pause                  # Wait for key press at the end
        """
    )
    
    parser.add_argument(
        '--configs',
        nargs='+',
        choices=list(CONFIGS.keys()) + ['all'],
        default=['all'],
        help='Configurations to build (default: all)'
    )
    
    parser.add_argument(
        '--rebuild',
        action='store_true',
        default=True,
        help='Force full rebuild (default: True)'
    )
    
    parser.add_argument(
        '--no-rebuild',
        action='store_false',
        dest='rebuild',
        help='Incremental build (only changed files)'
    )
    
    parser.add_argument(
        '--parallel',
        action='store_true',
        default=True,
        help='Enable parallel build (default: True)'
    )
    
    parser.add_argument(
        '--no-parallel',
        action='store_false',
        dest='parallel',
        help='Disable parallel build'
    )
    
    parser.add_argument(
        '--verbosity',
        choices=['quiet', 'minimal', 'normal', 'detailed', 'diagnostic'],
        default='quiet',
        help='MSBuild verbosity level (default: quiet)'
    )
    
    parser.add_argument(
        '--clean',
        action='store_true',
        default=True,
        help='Clean build artifacts after successful build (default: True)'
    )
    
    parser.add_argument(
        '--no-clean',
        action='store_false',
        dest='clean',
        help='Do not clean build artifacts'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List script configurations and exit'
    )
    
    parser.add_argument(
        '--list-project',
        action='store_true',
        help='List all configurations available in the project file and exit'
    )
    
    parser.add_argument(
        '--pause',
        action='store_true',
        help='Pause and wait for key press at the end'
    )
    
    parser.add_argument(
        '--no-optimizations',
        action='store_true',
        help='Disable additional build optimizations'
    )
    
    parser.add_argument(
        '--benchmark',
        action='store_true',
        help='Run performance comparison (with/without optimizations)'
    )

    parser.add_argument(
        '--vs-version',
        choices=['auto', '2026', '2022'],
        default='auto',
        help='Visual Studio version to use (default: auto - tries 2026 then 2022)'
    )

    args = parser.parse_args()
    
    # Get project paths early for list-project
    project_dir, project_file, plugins_dir = get_project_paths()
    
    # List project configurations
    if args.list_project:
        if not project_file.exists():
            print(f"ERROR: Project file not found: {project_file}")
            return 1
        print_available_configurations(project_file)
        return 0
    
    # List script configurations
    if args.list:
        print("Build script configurations (7-Zip 25.01, VS2026):")
        print("-" * 60)
        for name, config in CONFIGS.items():
            print(f"  {name:15s} -> {config.config} / {config.platform}")
        print(f"\nTotal: {len(CONFIGS)} configuration(s)")
        print("\nUse --list-project to see all configurations in the .vcxproj file")
        return 0
    
    # Find MSBuild
    msbuild_result = find_msbuild(args.vs_version)
    if not msbuild_result:
        print("ERROR: MSBuild not found!")
        print()
        print("Visual Studio 2026 Build Tools not found.")
        print("Checked locations:")
        print("  - C:\\Program Files\\Microsoft Visual Studio\\2026\\")
        print("  - C:\\Program Files (x86)\\Microsoft Visual Studio\\18\\")
        print("  - C:\\BuildTools\\")
        print()
        print("To install VS2026 Build Tools:")
        print("  choco install visualstudio2026buildtools")
        return 1
    msbuild_path, platform_toolset, vs_version_name = msbuild_result
    
    if not project_file.exists():
        print(f"ERROR: Project file not found: {project_file}")
        print()
        print("You need to create the VS2026 project file first.")
        print("Copy Nsis7z.vcxproj to Nsis7z_vs2026.vcxproj and update the toolset.")
        return 1
    
    # Determine configurations to build
    if 'all' in args.configs:
        configs_to_build = list(CONFIGS.values())
    else:
        configs_to_build = [CONFIGS[name] for name in args.configs]
    
    # Print header
    print("=" * 60)
    print(f"Building nsis7z plugin (7-Zip 25.01, VS2026) - {len(configs_to_build)} configuration(s)")
    print("=" * 60)
    print(f"Visual Studio: {vs_version_name} (toolset {platform_toolset})")
    print(f"MSBuild:   {msbuild_path}")
    print(f"Project:   {project_file}")
    print(f"Plugins:   {plugins_dir}")
    print(f"Rebuild:   {args.rebuild}")
    print(f"Verbosity: {args.verbosity}")
    print()
    
    # Print CPU and parallel build info
    use_optimizations = not args.no_optimizations
    print_cpu_info(args.parallel, use_optimizations)
    
    # Benchmark mode - compare with and without optimizations
    if args.benchmark and len(configs_to_build) == 1:
        config = configs_to_build[0]
        print("=" * 50)
        print("BENCHMARK MODE - Comparing optimization strategies")
        print("=" * 50)
        
        # Test without optimizations
        print("\n[1/2] Building WITHOUT optimizations...")
        success1, time1, _ = build_configuration(
            msbuild_path, project_file, config,
            rebuild=True, verbosity=args.verbosity,
            parallel=args.parallel, optimizations=False
        )
        
        if success1:
            copy_output(project_dir, plugins_dir, config)
        
        # Test with optimizations  
        print("\n[2/2] Building WITH optimizations...")
        success2, time2, _ = build_configuration(
            msbuild_path, project_file, config,
            rebuild=True, verbosity=args.verbosity,
            parallel=args.parallel, optimizations=True
        )
        
        if success2:
            copy_output(project_dir, plugins_dir, config)
        
        # Show comparison
        print("\n" + "=" * 50)
        print("BENCHMARK RESULTS")
        print("=" * 50)
        print(f"Without optimizations: {format_time(time1)}")
        print(f"With optimizations:    {format_time(time2)}")
        if time1 > time2:
            speedup = time1 / time2
            improvement = ((time1 - time2) / time1) * 100
            print(f"Speedup:              {speedup:.2f}x faster ({improvement:.1f}% improvement)")
        else:
            slowdown = time2 / time1  
            print(f"Slowdown:             {slowdown:.2f}x slower")
        
        if args.clean:
            clean_build_artifacts(project_dir, configs_to_build)
        
        return 0 if (success1 and success2) else 1
    
    # Build each configuration
    build_results = []
    total_start_time = time.time()

    if args.parallel and len(configs_to_build) > 1:
        build_results = _build_configs_parallel(
            msbuild_path, project_file, configs_to_build,
            rebuild=args.rebuild, verbosity=args.verbosity,
            parallel=args.parallel, optimizations=use_optimizations,
            project_dir=project_dir, plugins_dir=plugins_dir,
        )
    else:
        for i, config in enumerate(configs_to_build, 1):
            # Build
            success, build_time, _ = build_configuration(
                msbuild_path,
                project_file,
                config,
                rebuild=args.rebuild,
                verbosity=args.verbosity,
                parallel=args.parallel,
                optimizations=use_optimizations,
                counter=f"{i}/{len(configs_to_build)}"
            )

            if not success:
                print(f"ERROR: {config.name} build failed! (Time: {format_time(build_time)})")
                build_results.append((config, False, build_time, 0, None))
                continue

            # Copy output
            success, file_size, dest_path = copy_output(project_dir, plugins_dir, config)
            print(f"Build time: {format_time(build_time)}")
            build_results.append((config, success, build_time, file_size, dest_path))
    
    # Calculate total time
    total_time = time.time() - total_start_time
    
    # Summary
    print("\n" + "=" * 50)
    all_success = all(success for _, success, _, _, _ in build_results)
    
    if all_success:
        print("ALL BUILDS SUCCESSFUL!")
        print("=" * 50)
        print("\nPlugins copied to:")
        for config, _, build_time, file_size, dest_path in build_results:
            dest = dest_path if dest_path else plugins_dir / config.dest_dir / 'nsis7z.dll'
            print(f"  - {dest}")
        
        # Clean up
        if args.clean:
            print()
            clean_build_artifacts(project_dir, configs_to_build)
    else:
        print("SOME BUILDS FAILED!")
        print("=" * 50)
        print("\nFailed configurations:")
        for config, success, build_time, file_size, dest_path in build_results:
            if not success:
                print(f"  - {config.name}")
    
    # Show timing summary
    print("\n" + "-" * 50)
    print("Build Summary:")
    for config, success, build_time, file_size, dest_path in build_results:
        status = "OK" if success else "FAIL"
        size_str = f"{file_size:,} bytes" if file_size > 0 else "N/A"
        print(f"  {status} {config.name:15s} - {format_time(build_time):8s} - {size_str}")
    print("-" * 50)
    print(f"Total time: {format_time(total_time)}")
    print()
    
    # Pause if requested
    if args.pause:
        if not wait_for_key():
            print("Exiting...")
            return 1
    
    return 0 if all_success else 1


if __name__ == '__main__':
    sys.exit(main())
