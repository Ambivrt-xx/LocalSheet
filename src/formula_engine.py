"""
Lightweight formula engine: tokenizer → recursive-descent parser → evaluator.
Supports: SUM, AVERAGE, COUNT, MIN, MAX, IF, VLOOKUP,
          ABS, ROUND, SQRT, POWER, LEN, UPPER, LOWER, CONCATENATE, AND, OR, NOT,
          COUNTIF, SUMIF, AVERAGEIF, SUMIFS,
          TODAY, NOW, DATE, YEAR, MONTH, DAY,
          TEXT, TRIM, SUBSTITUTE, LEFT, RIGHT, MID
Operators: + - * /  >  <  >=  <=  =  <>  &
Cell refs: A1, $A$1   Ranges: A1:B10
"""
import re
from datetime import date, datetime


class FormulaError(Exception):
    pass


# ───────────────────── AST nodes ─────────────────────

class Number:
    def __init__(self, value):
        self.value = value


class StringNode:
    def __init__(self, value):
        self.value = value


class CellRef:
    def __init__(self, row, col):
        self.row = row
        self.col = col


class RangeRef:
    def __init__(self, r1, c1, r2, c2):
        self.r1 = min(r1, r2)
        self.c1 = min(c1, c2)
        self.r2 = max(r1, r2)
        self.c2 = max(c1, c2)


class UnaryOp:
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand


class BinOp:
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right


class FuncCall:
    def __init__(self, name, args):
        self.name = name
        self.args = args


# ───────────────────── Helpers ─────────────────────

def col_letters_to_index(letters):
    """A→0, B→1, …, Z→25, AA→26 …"""
    result = 0
    for ch in letters.upper():
        result = result * 26 + (ord(ch) - ord('A') + 1)
    return result - 1


def col_index_to_letters(index):
    """0→A, 1→B, …, 25→Z, 26→AA …"""
    result = ""
    index += 1
    while index > 0:
        index, rem = divmod(index - 1, 26)
        result = chr(ord('A') + rem) + result
    return result


_CELL_RE = re.compile(r'\$?([A-Za-z]+)\$?(\d+)$')


# ───────────────────── Tokenizer ─────────────────────

def tokenize(formula):
    tokens = []
    i = 0
    n = len(formula)
    while i < n:
        c = formula[i]
        if c.isspace():
            i += 1
            continue
        if c == '"':
            j = i + 1
            while j < n and formula[j] != '"':
                j += 1
            tokens.append(('STRING', formula[i + 1:j]))
            i = j + 1
            continue
        if c.isdigit() or (c == '.' and i + 1 < n and formula[i + 1].isdigit()):
            j = i
            while j < n and (formula[j].isdigit() or formula[j] == '.'):
                j += 1
            tokens.append(('NUMBER', float(formula[i:j])))
            i = j
            continue
        # unary minus
        if c == '-' and (not tokens or tokens[-1][0] in ('OP', 'LPAREN', 'COMMA', 'CMP', 'UOP')):
            tokens.append(('UOP', '-'))
            i += 1
            continue
        if c == '&':
            tokens.append(('OP', '&'))
            i += 1
            continue
        if c in '+-*/':
            tokens.append(('OP', c))
            i += 1
            continue
        if c == '(':
            tokens.append(('LPAREN', c))
            i += 1
            continue
        if c == ')':
            tokens.append(('RPAREN', c))
            i += 1
            continue
        if c == ',':
            tokens.append(('COMMA', c))
            i += 1
            continue
        if c == ':':
            tokens.append(('COLON', c))
            i += 1
            continue
        if c in '<>=':
            if i + 1 < n and formula[i + 1] == '=':
                tokens.append(('CMP', c + '='))
                i += 2
                continue
            if c == '<' and i + 1 < n and formula[i + 1] == '>':
                tokens.append(('CMP', '<>'))
                i += 2
                continue
            tokens.append(('CMP', c))
            i += 1
            continue
        m = re.match(r'[A-Za-z_$.][A-Za-z0-9_$.]*', formula[i:])
        if m:
            word = m.group(0)
            j = i + len(word)
            k = j
            while k < n and formula[k].isspace():
                k += 1
            if k < n and formula[k] == '(':
                tokens.append(('FUNC', word.upper()))
            else:
                cell_m = _CELL_RE.match(word)
                if cell_m:
                    col = col_letters_to_index(cell_m.group(1))
                    row = int(cell_m.group(2)) - 1
                    tokens.append(('CELL', (row, col)))
                else:
                    tokens.append(('NAME', word.upper()))
            i += len(word)
            continue
        raise FormulaError("#ERROR!")
    return tokens


# ───────────────────── Parser ─────────────────────

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, type_):
        tok = self.peek()
        if tok is None or tok[0] != type_:
            raise FormulaError("#ERROR!")
        return self.advance()

    def parse(self):
        node = self.parse_comparison()
        if self.pos < len(self.tokens):
            raise FormulaError("#ERROR!")
        return node

    def parse_comparison(self):
        left = self.parse_addition()
        while self.peek() and self.peek()[0] == 'CMP':
            op = self.advance()[1]
            right = self.parse_addition()
            left = BinOp(op, left, right)
        return left

    def parse_addition(self):
        left = self.parse_multiplication()
        while self.peek() and self.peek()[0] == 'OP' and self.peek()[1] in '+-':
            op = self.advance()[1]
            right = self.parse_multiplication()
            left = BinOp(op, left, right)
        return left

    def parse_multiplication(self):
        left = self.parse_unary()
        while self.peek() and self.peek()[0] == 'OP' and self.peek()[1] in '*/&':
            op = self.advance()[1]
            right = self.parse_unary()
            left = BinOp(op, left, right)
        return left

    def parse_unary(self):
        tok = self.peek()
        if tok and tok[0] == 'UOP':
            self.advance()
            return UnaryOp('-', self.parse_unary())
        return self.parse_primary()

    def parse_primary(self):
        tok = self.peek()
        if tok is None:
            raise FormulaError("#ERROR!")
        if tok[0] == 'NUMBER':
            self.advance()
            return Number(tok[1])
        if tok[0] == 'STRING':
            self.advance()
            return StringNode(tok[1])
        if tok[0] == 'NAME':
            self.advance()
            if tok[1] == 'TRUE':
                return Number(1)
            if tok[1] == 'FALSE':
                return Number(0)
            if tok[1] == 'PI':
                return Number(3.141592653589793)
            if tok[1] == 'E':
                return Number(2.718281828459045)
            raise FormulaError("#NAME?")
        if tok[0] == 'CELL':
            self.advance()
            row, col = tok[1]
            if self.peek() and self.peek()[0] == 'COLON':
                self.advance()
                nxt = self.peek()
                if nxt and nxt[0] == 'CELL':
                    self.advance()
                    r2, c2 = nxt[1]
                    return RangeRef(row, col, r2, c2)
                raise FormulaError("#ERROR!")
            return CellRef(row, col)
        if tok[0] == 'FUNC':
            self.advance()
            self.expect('LPAREN')
            args = []
            if self.peek() and self.peek()[0] != 'RPAREN':
                args.append(self.parse_comparison())
                while self.peek() and self.peek()[0] == 'COMMA':
                    self.advance()
                    args.append(self.parse_comparison())
            self.expect('RPAREN')
            return FuncCall(tok[1], args)
        if tok[0] == 'LPAREN':
            self.advance()
            node = self.parse_comparison()
            self.expect('RPAREN')
            return node
        raise FormulaError("#ERROR!")


def parse_formula(text):
    tokens = tokenize(text)
    if not tokens:
        return None
    return Parser(tokens).parse()


# ───────────────────── Evaluator ─────────────────────

def to_number(val):
    if isinstance(val, bool):
        return 1 if val else 0
    if isinstance(val, (int, float)):
        return val
    if isinstance(val, str):
        if val == '' or val.startswith('#'):
            return 0
        try:
            return float(val) if '.' in val or 'e' in val.lower() else int(val)
        except ValueError:
            raise FormulaError("#VALUE!")
    if val is None:
        return 0
    raise FormulaError("#VALUE!")


def to_bool(val):
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val != 0
    if isinstance(val, str):
        return val.upper() == 'TRUE'
    return False


def flatten(val):
    if isinstance(val, list):
        out = []
        for item in val:
            out.extend(flatten(item))
        return out
    return [val]


def numeric_values(vals):
    nums = []
    for v in vals:
        if isinstance(v, bool):
            nums.append(1 if v else 0)
        elif isinstance(v, (int, float)):
            nums.append(v)
        elif isinstance(v, str) and v and not v.startswith('#'):
            try:
                nums.append(float(v) if '.' in v or 'e' in v.lower() else int(v))
            except ValueError:
                pass
    return nums


def apply_op(op, left, right):
    if op == '+':
        return to_number(left) + to_number(right)
    if op == '-':
        return to_number(left) - to_number(right)
    if op == '*':
        return to_number(left) * to_number(right)
    if op == '&':
        def _to_text(v):
            if isinstance(v, bool):
                return "TRUE" if v else "FALSE"
            if isinstance(v, float) and v == int(v) and abs(v) < 1e15:
                return str(int(v))
            return str(v)
        return _to_text(left) + _to_text(right)
    if op == '/':
        r = to_number(right)
        if r == 0:
            raise FormulaError("#DIV/0!")
        return to_number(left) / r
    # comparisons
    try:
        ln, rn = to_number(left), to_number(right)
        if op == '>':
            return ln > rn
        if op == '<':
            return ln < rn
        if op == '>=':
            return ln >= rn
        if op == '<=':
            return ln <= rn
        if op == '=':
            return ln == rn
        if op == '<>':
            return ln != rn
    except FormulaError:
        ls, rs = str(left), str(right)
        if op == '>':
            return ls > rs
        if op == '<':
            return ls < rs
        if op == '>=':
            return ls >= rs
        if op == '<=':
            return ls <= rs
        if op == '=':
            return ls == rs
        if op == '<>':
            return ls != rs
    raise FormulaError("#ERROR!")


def eval_ast(node, get_cell, get_range):
    if isinstance(node, Number):
        return node.value
    if isinstance(node, StringNode):
        return node.value
    if isinstance(node, CellRef):
        return get_cell(node.row, node.col)
    if isinstance(node, RangeRef):
        return get_range(node.r1, node.c1, node.r2, node.c2)
    if isinstance(node, UnaryOp):
        return -to_number(eval_ast(node.operand, get_cell, get_range))
    if isinstance(node, BinOp):
        left = eval_ast(node.left, get_cell, get_range)
        right = eval_ast(node.right, get_cell, get_range)
        return apply_op(node.op, left, right)
    if isinstance(node, FuncCall):
        return eval_func(node, get_cell, get_range)
    raise FormulaError("#ERROR!")


def _to_date(val):
    """Convert a value to a datetime.date, or None."""
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, (int, float)):
        # Excel serial date (days since 1899-12-30)
        try:
            return date(1899, 12, 30) + __import__('datetime').timedelta(days=int(val))
        except (ValueError, OverflowError):
            return None
    if isinstance(val, str):
        for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d'):
            try:
                return datetime.strptime(val, fmt).date()
            except ValueError:
                pass
    return None


def _to_datetime(val):
    """Convert a value to a datetime.datetime, or None."""
    if isinstance(val, datetime):
        return val
    if isinstance(val, date):
        return datetime(val.year, val.month, val.day)
    if isinstance(val, str):
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d',
                    '%m/%d/%Y %H:%M:%S', '%m/%d/%Y'):
            try:
                return datetime.strptime(val, fmt)
            except ValueError:
                pass
    return None


def _match_criteria(value, criteria):
    """Check if *value* matches *criteria* (number, string, or comparison string)."""
    if isinstance(criteria, str):
        m = re.match(r'^(>=|<=|<>|>|<|=)(.*)$', criteria)
        if m:
            op = m.group(1)
            operand = m.group(2).strip()
            try:
                operand_num = float(operand)
                value_num = to_number(value)
                if op == '>': return value_num > operand_num
                if op == '<': return value_num < operand_num
                if op == '>=': return value_num >= operand_num
                if op == '<=': return value_num <= operand_num
                if op == '=': return value_num == operand_num
                if op == '<>': return value_num != operand_num
            except FormulaError:
                if op == '=': return str(value) == operand
                if op == '<>': return str(value) != operand
            return False
        # Wildcard matching
        if '*' in criteria or '?' in criteria:
            pattern = re.escape(criteria).replace(r'\*', '.*').replace(r'\?', '.')
            return bool(re.match(f'^{pattern}$', str(value)))
        # Direct equality
        try:
            return to_number(value) == to_number(criteria)
        except FormulaError:
            return str(value).lower() == str(criteria).lower()
    # Numeric criteria
    try:
        return to_number(value) == to_number(criteria)
    except FormulaError:
        return False


def eval_func(node, get_cell, get_range):
    name = node.name
    args = node.args

    if name == 'IF':
        cond = to_bool(eval_ast(args[0], get_cell, get_range))
        if cond:
            return eval_ast(args[1], get_cell, get_range)
        elif len(args) > 2:
            return eval_ast(args[2], get_cell, get_range)
        return False

    if name == 'VLOOKUP':
        lookup = eval_ast(args[0], get_cell, get_range)
        if isinstance(args[1], RangeRef):
            data = get_range(args[1].r1, args[1].c1, args[1].r2, args[1].c2)
        else:
            data = eval_ast(args[1], get_cell, get_range)
            if not isinstance(data, list):
                data = [[data]]
        col_idx = int(to_number(eval_ast(args[2], get_cell, get_range)))
        for row in data:
            if row and (row[0] == lookup or str(row[0]) == str(lookup)):
                if 1 <= col_idx <= len(row):
                    return row[col_idx - 1]
        return '#N/A'

    if name == 'HLOOKUP':
        lookup = eval_ast(args[0], get_cell, get_range)
        if isinstance(args[1], RangeRef):
            data = get_range(args[1].r1, args[1].c1, args[1].r2, args[1].c2)
        else:
            data = eval_ast(args[1], get_cell, get_range)
            if not isinstance(data, list):
                data = [[data]]
        row_idx = int(to_number(eval_ast(args[2], get_cell, get_range)))
        if data:
            first_row = data[0]
            for ci, cell_val in enumerate(first_row):
                if cell_val == lookup or str(cell_val) == str(lookup):
                    if 1 <= row_idx <= len(data):
                        return data[row_idx - 1][ci]
        return '#N/A'

    if name == 'INDEX':
        if isinstance(args[0], RangeRef):
            data = get_range(args[0].r1, args[0].c1, args[0].r2, args[0].c2)
        else:
            data = eval_ast(args[0], get_cell, get_range)
            if not isinstance(data, list):
                data = [[data]]
        row_num = int(to_number(eval_ast(args[1], get_cell, get_range)))
        col_num = int(to_number(eval_ast(args[2], get_cell, get_range))) if len(args) > 2 else 1
        try:
            if isinstance(data[0], list):
                return data[row_num - 1][col_num - 1]
            return data[row_num - 1]
        except (IndexError, TypeError):
            return '#REF!'

    if name == 'MATCH':
        lookup = eval_ast(args[0], get_cell, get_range)
        if isinstance(args[1], RangeRef):
            data = get_range(args[1].r1, args[1].c1, args[1].r2, args[1].c2)
        else:
            data = eval_ast(args[1], get_cell, get_range)
            if not isinstance(data, list):
                data = [data]
        match_type = int(to_number(eval_ast(args[2], get_cell, get_range))) if len(args) > 2 else 1
        flat = flatten(data)
        if match_type == 0:
            for i, v in enumerate(flat):
                if str(v) == str(lookup) or v == lookup:
                    return i + 1
            return '#N/A'
        elif match_type == 1:
            best = None
            for i, v in enumerate(flat):
                try:
                    if to_number(v) <= to_number(lookup):
                        best = i + 1
                    else:
                        break
                except FormulaError:
                    pass
            return best or '#N/A'
        else:
            best = None
            for i, v in enumerate(flat):
                try:
                    if to_number(v) >= to_number(lookup):
                        best = i + 1
                    else:
                        break
                except FormulaError:
                    pass
            return best or '#N/A'

    if name == 'XLOOKUP':
        lookup = eval_ast(args[0], get_cell, get_range)
        if isinstance(args[1], RangeRef):
            search_data = flatten(get_range(args[1].r1, args[1].c1, args[1].r2, args[1].c2))
        else:
            search_data = flatten([eval_ast(args[1], get_cell, get_range)])
        if isinstance(args[2], RangeRef):
            return_data = flatten(get_range(args[2].r1, args[2].c1, args[2].r2, args[2].c2))
        else:
            return_data = flatten([eval_ast(args[2], get_cell, get_range)])
        not_found = eval_ast(args[3], get_cell, get_range) if len(args) > 3 else '#N/A'
        for i, v in enumerate(search_data):
            if str(v) == str(lookup) or v == lookup:
                if i < len(return_data):
                    return return_data[i]
        return not_found

    if name == 'AND':
        for a in args:
            if not to_bool(eval_ast(a, get_cell, get_range)):
                return False
        return True

    if name == 'OR':
        for a in args:
            if to_bool(eval_ast(a, get_cell, get_range)):
                return True
        return False

    if name == 'NOT':
        return not to_bool(eval_ast(args[0], get_cell, get_range))

    if name == 'CONCATENATE':
        return ''.join(str(eval_ast(a, get_cell, get_range)) for a in args)

    if name == 'ABS':
        return abs(to_number(eval_ast(args[0], get_cell, get_range)))
    if name == 'ROUND':
        v = to_number(eval_ast(args[0], get_cell, get_range))
        d = int(to_number(eval_ast(args[1], get_cell, get_range))) if len(args) > 1 else 0
        return round(v, d)
    if name == 'ROUNDUP':
        import math
        v = to_number(eval_ast(args[0], get_cell, get_range))
        d = int(to_number(eval_ast(args[1], get_cell, get_range))) if len(args) > 1 else 0
        factor = 10 ** d
        return math.ceil(v * factor) / factor if v >= 0 else -math.ceil(-v * factor) / factor
    if name == 'ROUNDDOWN':
        import math
        v = to_number(eval_ast(args[0], get_cell, get_range))
        d = int(to_number(eval_ast(args[1], get_cell, get_range))) if len(args) > 1 else 0
        factor = 10 ** d
        return math.floor(v * factor) / factor if v >= 0 else -math.floor(-v * factor) / factor
    if name == 'SQRT':
        v = to_number(eval_ast(args[0], get_cell, get_range))
        if v < 0:
            raise FormulaError("#NUM!")
        return v ** 0.5
    if name == 'POWER':
        base = to_number(eval_ast(args[0], get_cell, get_range))
        exp = to_number(eval_ast(args[1], get_cell, get_range))
        return base ** exp
    if name == 'LEN':
        return len(str(eval_ast(args[0], get_cell, get_range)))
    if name == 'UPPER':
        return str(eval_ast(args[0], get_cell, get_range)).upper()
    if name == 'LOWER':
        return str(eval_ast(args[0], get_cell, get_range)).lower()

    # ── String functions: LEFT, RIGHT, MID ──
    if name == 'LEFT':
        text = str(eval_ast(args[0], get_cell, get_range))
        n = int(to_number(eval_ast(args[1], get_cell, get_range))) if len(args) > 1 else 1
        return text[:n]
    if name == 'RIGHT':
        text = str(eval_ast(args[0], get_cell, get_range))
        n = int(to_number(eval_ast(args[1], get_cell, get_range))) if len(args) > 1 else 1
        return text[-n:] if n > 0 else ""
    if name == 'MID':
        text = str(eval_ast(args[0], get_cell, get_range))
        start = int(to_number(eval_ast(args[1], get_cell, get_range)))
        length = int(to_number(eval_ast(args[2], get_cell, get_range)))
        return text[start - 1:start - 1 + length]
    if name == 'TRIM':
        return str(eval_ast(args[0], get_cell, get_range)).strip()
    if name == 'SUBSTITUTE':
        text = str(eval_ast(args[0], get_cell, get_range))
        old = str(eval_ast(args[1], get_cell, get_range))
        new = str(eval_ast(args[2], get_cell, get_range))
        if len(args) > 3:
            instance = int(to_number(eval_ast(args[3], get_cell, get_range)))
            # Replace only the Nth occurrence
            idx = -1
            for _ in range(instance):
                idx = text.find(old, idx + 1)
                if idx == -1:
                    return text
            return text[:idx] + new + text[idx + len(old):]
        return text.replace(old, new)
    if name == 'TEXT':
        val = eval_ast(args[0], get_cell, get_range)
        fmt = str(eval_ast(args[1], get_cell, get_range))
        if isinstance(val, (int, float)):
            if fmt == '0':
                return str(int(round(val)))
            if fmt == '0.00':
                return f"{val:.2f}"
            if fmt.startswith('0.'):
                decimals = len(fmt) - 2
                return f"{val:.{decimals}f}"
            if '%' in fmt:
                return f"{val * 100:.0f}%"
            if fmt == '#,##0':
                return f"{int(round(val)):,}"
        return str(val)
    if name == 'REPT':
        text = str(eval_ast(args[0], get_cell, get_range))
        n = int(to_number(eval_ast(args[1], get_cell, get_range)))
        return text * n

    # ── Date functions ──
    if name == 'TODAY':
        return date.today()
    if name == 'NOW':
        return datetime.now()
    if name == 'DATE':
        y = int(to_number(eval_ast(args[0], get_cell, get_range)))
        m = int(to_number(eval_ast(args[1], get_cell, get_range)))
        d = int(to_number(eval_ast(args[2], get_cell, get_range)))
        try:
            return date(y, m, d)
        except ValueError:
            raise FormulaError("#NUM!")
    if name == 'YEAR':
        d = _to_date(eval_ast(args[0], get_cell, get_range))
        return d.year if d else 0
    if name == 'MONTH':
        d = _to_date(eval_ast(args[0], get_cell, get_range))
        return d.month if d else 0
    if name == 'DAY':
        d = _to_date(eval_ast(args[0], get_cell, get_range))
        return d.day if d else 0
    if name == 'HOUR':
        dt = _to_datetime(eval_ast(args[0], get_cell, get_range))
        return dt.hour if dt else 0
    if name == 'MINUTE':
        dt = _to_datetime(eval_ast(args[0], get_cell, get_range))
        return dt.minute if dt else 0
    if name == 'SECOND':
        dt = _to_datetime(eval_ast(args[0], get_cell, get_range))
        return dt.second if dt else 0
    if name == 'WEEKDAY':
        d = _to_date(eval_ast(args[0], get_cell, get_range))
        if not d:
            return 0
        # Sunday=1 ... Saturday=7 (Excel default)
        return d.isoweekday() % 7 + 1
    if name == 'DATEDIF':
        d1 = _to_date(eval_ast(args[0], get_cell, get_range))
        d2 = _to_date(eval_ast(args[1], get_cell, get_range))
        unit = str(eval_ast(args[2], get_cell, get_range)).upper()
        if not d1 or not d2:
            return 0
        if unit == 'D':
            return (d2 - d1).days
        if unit == 'M':
            return (d2.year - d1.year) * 12 + (d2.month - d1.month)
        if unit == 'Y':
            return d2.year - d1.year - (1 if (d2.month, d2.day) < (d1.month, d1.day) else 0)
        raise FormulaError("#NUM!")

    # ── Conditional aggregation: COUNTIF, SUMIF, AVERAGEIF, SUMIFS ──
    if name == 'COUNTIF':
        rng = flatten([eval_ast(args[0], get_cell, get_range)])
        criteria = eval_ast(args[1], get_cell, get_range)
        return sum(1 for v in rng if _match_criteria(v, criteria))
    if name == 'SUMIF':
        rng = flatten([eval_ast(args[0], get_cell, get_range)])
        criteria = eval_ast(args[1], get_cell, get_range)
        if len(args) > 2:
            sum_rng = flatten([eval_ast(args[2], get_cell, get_range)])
        else:
            sum_rng = rng
        total = 0
        for i, v in enumerate(rng):
            if _match_criteria(v, criteria):
                if i < len(sum_rng):
                    total += to_number(sum_rng[i]) if not str(sum_rng[i]).startswith('#') else 0
        return total
    if name == 'AVERAGEIF':
        rng = flatten([eval_ast(args[0], get_cell, get_range)])
        criteria = eval_ast(args[1], get_cell, get_range)
        if len(args) > 2:
            avg_rng = flatten([eval_ast(args[2], get_cell, get_range)])
        else:
            avg_rng = rng
        total = 0
        count = 0
        for i, v in enumerate(rng):
            if _match_criteria(v, criteria):
                if i < len(avg_rng):
                    sv = avg_rng[i]
                    if not str(sv).startswith('#') and sv != '':
                        total += to_number(sv)
                        count += 1
        if count == 0:
            raise FormulaError("#DIV/0!")
        return total / count
    if name == 'SUMIFS':
        sum_rng = flatten([eval_ast(args[0], get_cell, get_range)])
        total = 0
        for i in range(len(sum_rng)):
            match = True
            for j in range(1, len(args), 2):
                if j + 1 >= len(args):
                    break
                crng = flatten([eval_ast(args[j], get_cell, get_range)])
                crit = eval_ast(args[j + 1], get_cell, get_range)
                if i < len(crng) and not _match_criteria(crng[i], crit):
                    match = False
                    break
            if match:
                sv = sum_rng[i]
                if not str(sv).startswith('#') and sv != '':
                    total += to_number(sv)
        return total
    if name == 'COUNTA':
        vals = flatten([eval_ast(a, get_cell, get_range) for a in args])
        return sum(1 for v in vals if v is not None and v != "" and not str(v).startswith('#'))
    if name == 'COUNTBLANK':
        vals = flatten([eval_ast(a, get_cell, get_range) for a in args])
        return sum(1 for v in vals if v is None or v == "")
    if name == 'RANK':
        val = to_number(eval_ast(args[0], get_cell, get_range))
        rng = flatten([eval_ast(args[1], get_cell, get_range)])
        nums = numeric_values(rng)
        descending = True
        if len(args) > 2:
            descending = to_number(eval_ast(args[2], get_cell, get_range)) == 0
        sorted_nums = sorted(nums, reverse=descending)
        try:
            return sorted_nums.index(val) + 1
        except ValueError:
            return '#N/A'
    if name == 'IFERROR':
        try:
            return eval_ast(args[0], get_cell, get_range)
        except FormulaError:
            return eval_ast(args[1], get_cell, get_range) if len(args) > 1 else ""

    # aggregation functions
    vals = flatten([eval_ast(a, get_cell, get_range) for a in args])
    nums = numeric_values(vals)
    if name == 'SUM':
        return sum(nums)
    if name == 'AVERAGE':
        if not nums:
            raise FormulaError("#DIV/0!")
        return sum(nums) / len(nums)
    if name == 'COUNT':
        return len(nums)
    if name == 'MIN':
        return min(nums) if nums else 0
    if name == 'MAX':
        return max(nums) if nums else 0
    if name == 'STDEV':
        if len(nums) < 2:
            raise FormulaError("#DIV/0!")
        mean = sum(nums) / len(nums)
        variance = sum((x - mean) ** 2 for x in nums) / (len(nums) - 1)
        return variance ** 0.5
    if name == 'VAR':
        if len(nums) < 2:
            raise FormulaError("#DIV/0!")
        mean = sum(nums) / len(nums)
        return sum((x - mean) ** 2 for x in nums) / (len(nums) - 1)
    if name == 'MEDIAN':
        if not nums:
            return 0
        s = sorted(nums)
        n = len(s)
        return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
    if name == 'MODE':
        if not nums:
            return '#N/A'
        from collections import Counter
        counts = Counter(nums)
        return counts.most_common(1)[0][0]

    raise FormulaError("#NAME?")


# ───────────────────── Recalculation ─────────────────────

def parse_value(raw):
    """Parse a non-formula raw string into int / float / str."""
    if raw is None or raw == "":
        return ""
    if isinstance(raw, (int, float)):
        return raw
    s = str(raw).strip()
    if s == "":
        return ""
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return raw


def format_value(val):
    """Convert a computed value to display string."""
    if val is None:
        return ""
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(val, date):
        return val.strftime("%Y-%m-%d")
    if isinstance(val, float):
        if val == int(val) and abs(val) < 1e15:
            return str(int(val))
        return str(round(val, 10))
    return str(val)


def recalculate(worksheet):
    """
    Recalculate every formula cell in *worksheet*.
    Returns list of (row, col) whose displayed value changed.
    """
    cache = {}
    visiting = set()
    changed = []

    def get_cell(row, col):
        cell = worksheet.cells.get((row, col))
        if cell is None:
            return ""
        raw = cell.raw
        if isinstance(raw, str) and raw.startswith('='):
            if (row, col) in visiting:
                result = '#CIRC!'
                if cell.value != result:
                    cell.value = result
                    changed.append((row, col))
                return result
            if (row, col) in cache:
                return cache[(row, col)]
            visiting.add((row, col))
            try:
                formula_text = raw[1:]
                # Resolve named ranges
                named = getattr(worksheet, 'named_ranges', {})
                if named:
                    formula_text = _resolve_named_ranges(formula_text, named)
                ast = parse_formula(formula_text)
                if ast is None:
                    result = ""
                else:
                    result = eval_ast(ast, get_cell, get_range)
            except FormulaError as e:
                result = str(e)
            except ZeroDivisionError:
                result = '#DIV/0!'
            except Exception:
                result = '#ERROR'
            finally:
                visiting.discard((row, col))
            cache[(row, col)] = result
            old = cell.value
            cell.value = result
            if format_value(old) != format_value(result):
                changed.append((row, col))
            return result
        else:
            return cell.value if cell.value is not None else ""

    def get_range(r1, c1, r2, c2):
        result = []
        for r in range(r1, r2 + 1):
            row_vals = []
            for c in range(c1, c2 + 1):
                row_vals.append(get_cell(r, c))
            result.append(row_vals)
        return result

    for (row, col), cell in list(worksheet.cells.items()):
        if isinstance(cell.raw, str) and cell.raw.startswith('='):
            get_cell(row, col)

    return changed


def resolve_name(name, worksheet):
    """Resolve a named range to a (r1, c1, r2, c2) tuple, or None."""
    if hasattr(worksheet, 'named_ranges'):
        nr = worksheet.named_ranges.get(name.upper())
        if nr:
            return nr
    return None


def _resolve_named_ranges(formula_text, named):
    """Replace named range references in formula text with A1:B2 range strings."""
    for name, (r1, c1, r2, c2) in named.items():
        ref = f"{col_index_to_letters(c1)}{r1+1}:{col_index_to_letters(c2)}{r2+1}"
        pattern = re.compile(r'\b' + re.escape(name) + r'\b', re.IGNORECASE)
        formula_text = pattern.sub(ref, formula_text)
    return formula_text