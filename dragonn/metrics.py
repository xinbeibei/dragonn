from __future__ import absolute_import, division, print_function
import numpy as np
from collections import OrderedDict
from sklearn.metrics import auc, precision_recall_curve, roc_auc_score
from dragonn.prg import create_prg_curve, calc_auprg


class IgnoreNumpyErrors(object):
    # Ignore warnings from comparing with nan, division by 0 and numerical
    # overflow/underflow

    def __enter__(self):
        self.prev_error_handler = np.seterr(all='ignore')

    def __exit__(self, exc_type, exc_val, exc_tb):
        np.seterr(**self.prev_error_handler)


def positive_accuracy(labels, predictions, threshold=0.5):
    return 100 * (predictions[labels] > threshold).mean()


def negative_accuracy(labels, predictions, threshold=0.5):
    return 100 * (predictions[~labels] < threshold).mean()


def balanced_accuracy(labels, predictions, threshold=0.5):
    return (positive_accuracy(labels, predictions, threshold) +
            negative_accuracy(labels, predictions, threshold)) / 2


def auROC(labels, predictions):
    return roc_auc_score(labels, predictions)


def auPRC(labels, predictions):
    precision, recall = precision_recall_curve(labels, predictions)[:2]
    return auc(recall, precision)


def auPRG(labels, predictions):
    return calc_auprg(create_prg_curve(labels, predictions))


def recall_at_precision_threshold(labels, predictions, precision_threshold):
    precision, recall = precision_recall_curve(labels, predictions)[:2]
    return 100 * recall[np.searchsorted(precision - precision_threshold, 0)]


class ClassificationResult(object):

    def __init__(self, labels, predictions, task_names=None):
        assert labels.dtype == bool
        self.results = [OrderedDict((
            ('Balanced accuracy', balanced_accuracy(
                task_labels, task_predictions)),
            ('auROC', auROC(task_labels, task_predictions)),
            ('auPRC', auPRC(task_labels, task_predictions)),
            ('auPRG', auPRG(task_labels, task_predictions)),
            ('Recall at 5% FDR', recall_at_precision_threshold(
                task_labels, task_predictions, 0.95)),
            ('Recall at 10% FDR', recall_at_precision_threshold(
                task_labels, task_predictions, 0.9)),
            ('Recall at 20% FDR', recall_at_precision_threshold(
                task_labels, task_predictions, 0.8)),
            ('Num Positives', task_labels.sum()),
            ('Num Negatives', (1 - task_labels).sum())
        )) for task_labels, task_predictions in zip(labels.T, predictions.T)]
        self.task_names = task_names
        self.multitask = labels.shape[1] > 1

    def __str__(self):
        return '\n'.join(
            '{}Balanced Accuracy: {:.2f}%\t '
            'auROC: {:.3f}\t auPRC: {:.3f}\t auPRG: {:.3f}\n'
            'Recall at 5%|10%|20% FDR: {:.1f}%|{:.1f}%|{:.1f}%\t '
            'Num Positives: {}\t Num Negatives: {}\t '.format(
                '{}: '.format('Task {}'.format(
                    self.task_names[task_index]
                    if self.task_names is not None else task_index))
                if self.multitask else '', *results.values())
            for task_index, results in enumerate(self.results))

    def __getitem__(self, item):
        return self.results[item]
