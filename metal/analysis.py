from collections import Counter, defaultdict
import numpy as np


def error_buckets(gold, pred, X=None):
    """Group items by error buckets
    
    Args:
        gold: a torch.Tensor of gold labels (ints)
        pred: a torch.Tensor of predictions (ints)
        X: an iterable of items
    Returns:
        buckets: A dict of items where buckets[i,j] is a list of items with
            predicted label i and true label j. If X is None, return indices
            instead.

    For a binary problem with (1=positive, 2=negative):
        buckets[1,1] = true positives
        buckets[1,2] = false positives
        buckets[2,1] = false negatives
        buckets[2,2] = true negatives
    """
    buckets = defaultdict(list)
    for i, (y, l) in enumerate(zip(gold.numpy(), pred.numpy())):
        buckets[y,l].append(X[i] if X is not None else i)
    return buckets


def confusion_matrix(gold, pred, null_pred=False, null_gold=False, 
    normalize=False, pretty=False):
    """A shortcut method for building a confusion matrix all at once.
    
    Args:
        gold: a torch.Tensor of gold labels (ints)
        pred: a torch.Tensor of predictions (ints)
        normalize: if True, divide counts by the total number of items
        pretty: if True, pretty-print the matrix
    """    
    conf = ConfusionMatrix(null_pred=null_pred, null_gold=null_gold)
    conf.add(gold, pred)
    mat = conf.compile()
    
    if normalize:
        mat = mat / len(gold)

    if pretty:
        conf.display()

    return mat

class ConfusionMatrix(object):
    """
    An iteratively built abstention-aware confusion matrix with pretty printing

    Assumed axes are true label on top, predictions on the side.
    """
    def __init__(self, null_pred=False, null_gold=False):
        """
        Args:
            null_pred: If True, show the row corresponding to null predictions
            null_gold: If True, show the col corresponding to null gold labels

        """
        self.counter = Counter()
        self.mat = None
        self.null_pred = null_pred
        self.null_gold = null_gold

    def __repr__(self):
        if self.mat is None:
            self.compile()
        return str(self.mat)

    def add(self, gold, pred):
        """
        Args:
            gold: a torch.Tensor of gold labels (ints)
            pred: a torch.Tensor of predictions (ints)
        """
        self.counter.update(zip(gold.numpy(), pred.numpy()))
    
    def compile(self, trim=True):
        k = max([max(tup) for tup in self.counter.keys()]) + 1  # include 0

        mat = np.zeros((k, k), dtype=int)
        for (p, y), v in self.counter.items():
            mat[p, y] = v
        
        if trim and not self.null_pred:
            mat = mat[1:, :]
        if trim and not self.null_gold:
            mat = mat[:, 1:]

        self.mat = mat
        return mat

    def display(self, counts=True, indent=0, spacing=2, decimals=3, 
        mark_diag=True):
        mat = self.compile(trim=False)
        m, n = mat.shape
        tab = ' ' * spacing
        margin = ' ' * indent

        # Print headers
        s = margin + ' ' * (5 + spacing)
        for j in range(n):
            if j == 0 and not self.null_gold:
                continue
            s += f" y={j} " + tab
        print(s)

        # Print data
        for i in range(m):
            # Skip null predictions row if necessary
            if i == 0 and not self.null_pred:
                continue
            s = margin + f" l={i} " + tab
            for j in range(n):
                # Skip null gold if necessary
                if j == 0 and not self.null_gold:
                    continue
                else:
                    if i == j and mark_diag and not counts:
                        s = s[:-1] + '*'
                    if counts:
                        s += f"{mat[i,j]:^5d}" + tab
                    else:
                        s += f"{mat[i,j]/sum(mat[i,1:]):>5.3f}" + tab
            print(s)