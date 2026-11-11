#!/usr/bin/env bash
# Rebuild graphify knowledge graphs for the directories listed in .github/graphify/targets.txt.
# Used by the VS Code tasks (manual) and by .github/workflows/graphify.yml (CI).
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: .github/graphify/update.sh [options] [DIR ...]

Rebuild graphify knowledge graphs. Each DIR gets its own graph in DIR/graphify-out/.
With no DIR, every target in .github/graphify/targets.txt is rebuilt.

Options:
  --changed REF   only rebuild targets with files changed between REF and HEAD
  --full          also run semantic (LLM) extraction on docs/papers/images (needs an API key)
  --code-only     local AST extraction only: no API key, no network
  --no-viz        skip graph.html generation
  --list          print the configured target directories and exit
  -h, --help      show this help

Mode precedence: --full/--code-only > the target's mode column > $GRAPHIFY_MODE > code-only.

Environment:
  GRAPHIFY_MODE   default mode (code-only|full)
  GRAPHIFY_BIN    graphify executable (default: graphify)
EOF
}

repo_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$repo_root"

targets_file=".github/graphify/targets.txt"
graphify_bin=${GRAPHIFY_BIN:-graphify}
forced_mode=""
changed_ref=""
no_viz=0
list_only=0
explicit_dirs=()

warn() {
    if [[ -n ${GITHUB_ACTIONS:-} ]]; then
        echo "::warning::$*"
    else
        echo "warning: $*" >&2
    fi
}

die() {
    if [[ -n ${GITHUB_ACTIONS:-} ]]; then
        echo "::error::$*"
    else
        echo "error: $*" >&2
    fi
    exit 1
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --changed)
            [[ $# -ge 2 ]] || die "--changed needs a git ref, e.g. --changed origin/main"
            changed_ref=$2
            shift 2
            ;;
        --full) forced_mode=full; shift ;;
        --code-only) forced_mode=code-only; shift ;;
        --no-viz) no_viz=1; shift ;;
        --list) list_only=1; shift ;;
        -h | --help) usage; exit 0 ;;
        --) shift; explicit_dirs+=("$@"); break ;;
        -*) die "unknown option '$1' (see --help)" ;;
        *) explicit_dirs+=("$1"); shift ;;
    esac
done

normalize_dir() {
    local d=${1%/}
    d=${d#./}
    [[ -z $d ]] && d="."
    printf '%s\n' "$d"
}

# Prints "dir<TAB>mode" for every configured target (mode may be empty).
read_targets() {
    [[ -f $targets_file ]] || return 0
    local line dir mode
    while IFS= read -r line || [[ -n $line ]]; do
        line=${line%%#*}
        read -r dir mode _ <<<"$line" || true
        [[ -z ${dir:-} ]] && continue
        printf '%s\t%s\n' "$(normalize_dir "$dir")" "${mode:-}"
    done <"$targets_file"
}

configured_mode_for() {
    local want=$1 dir mode
    while IFS=$'\t' read -r dir mode; do
        if [[ $dir == "$want" ]]; then
            printf '%s\n' "$mode"
            return 0
        fi
    done < <(read_targets)
    printf '\n'
}

if [[ $list_only -eq 1 ]]; then
    read_targets | cut -f1
    exit 0
fi

# True when files under $1 (excluding graphify output) are in the changed-file list.
dir_changed() {
    local dir=$1
    awk -v p="$dir/" -v root="$([[ $dir == "." ]] && echo 1 || echo 0)" '
        /(^|\/)graphify-out\// { next }
        root == 1 || index($0, p) == 1 { found = 1 }
        END { exit !found }
    ' <<<"$changed_files"
}

# Build the work list: "dir<TAB>mode".
work=()
if [[ ${#explicit_dirs[@]} -gt 0 ]]; then
    for d in "${explicit_dirs[@]}"; do
        d=$(normalize_dir "$d")
        work+=("$d"$'\t'"$(configured_mode_for "$d")")
    done
else
    mapfile -t work < <(read_targets)
fi

if [[ -n $changed_ref ]]; then
    if git rev-parse --verify --quiet "${changed_ref}^{commit}" >/dev/null; then
        changed_files=$(git diff --name-only "$changed_ref" HEAD --)
        if grep -qxF "$targets_file" <<<"$changed_files"; then
            echo "$targets_file changed: rebuilding every selected target."
        else
            filtered=()
            for entry in "${work[@]}"; do
                if dir_changed "${entry%%$'\t'*}"; then
                    filtered+=("$entry")
                fi
            done
            work=("${filtered[@]+"${filtered[@]}"}")
        fi
    else
        warn "cannot resolve '$changed_ref' (first push or force-push?): rebuilding every selected target."
    fi
fi

if [[ ${#work[@]} -eq 0 ]]; then
    echo "graphify: nothing to rebuild."
    exit 0
fi

if ! command -v "$graphify_bin" >/dev/null 2>&1; then
    die "graphify CLI not found. Install it with: pipx install graphifyy (or: uv tool install graphifyy, pip install graphifyy)"
fi

have_llm_backend() {
    [[ -n ${GRAPHIFY_BACKEND:-} && ${GRAPHIFY_BACKEND} != none ]] && return 0
    local v
    for v in ANTHROPIC_API_KEY OPENAI_API_KEY GEMINI_API_KEY GOOGLE_API_KEY MOONSHOT_API_KEY DEEPSEEK_API_KEY; do
        [[ -n ${!v:-} ]] && return 0
    done
    return 1
}

build_one() {
    local dir=$1 mode=$2
    if [[ ! -d $dir ]]; then
        warn "target '$dir' does not exist: skipped (fix $targets_file)"
        return 1
    fi
    if [[ $mode == full ]] && ! have_llm_backend; then
        warn "'$dir' wants full extraction but no LLM API key is set: falling back to code-only."
        mode=code-only
    fi

    local extract_args=(extract "$dir")
    local cluster_args=(cluster-only "$dir")
    if [[ $mode == code-only ]]; then
        extract_args+=(--code-only)
        cluster_args+=(--no-label)
    fi
    [[ $no_viz -eq 1 ]] && cluster_args+=(--no-viz)

    echo "==> graphify $dir ($mode)"
    "$graphify_bin" "${extract_args[@]}" && "$graphify_bin" "${cluster_args[@]}"
}

failed=()
for entry in "${work[@]}"; do
    dir=${entry%%$'\t'*}
    mode=${entry#*$'\t'}
    mode=${forced_mode:-${mode:-${GRAPHIFY_MODE:-code-only}}}
    case $mode in
        code-only | full) ;;
        *) warn "'$dir' has unknown mode '$mode': using code-only"; mode=code-only ;;
    esac
    build_one "$dir" "$mode" || failed+=("$dir")
done

if [[ ${#failed[@]} -gt 0 ]]; then
    die "graphify failed for: ${failed[*]}"
fi
echo "graphify: done."
