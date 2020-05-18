/*
Quiz (test) create/update validation for QuestBox project
*/

import { path, equals, reduce, is } from 'rambda';
import { isEmpty, addIndex } from 'ramda';

import i18n from '../../i18n';

const reduceIndexed = addIndex(reduce);

const validateChoiceQuestionValues = values => {
  return reduceIndexed((acc, answer, idx) => {
    if (!path('text', answer)) {
      acc[idx] = { text: i18n.t('common:required_field') };
    }

    return acc;
  }, [])(values.answers);
};

const validateCodeQuestionValues = values => {
  return reduceIndexed((acc, testCase, idx) => {
    if (!path('input', testCase)) {
      acc[idx] = acc[idx] || {};
      acc[idx].input = i18n.t('common:required_field');
    }
    if (!path('output', testCase)) {
      acc[idx] = acc[idx] || {};
      acc[idx].output = i18n.t('common:required_field');
    }

    return acc;
  }, [])(values.testcases);
};

export const validate = values => {
  const errors = {};
  if (!values.name) {
    errors.name = i18n.t('common:required_field');
  }
  if (path('city.label', values) && !path('city.value', values)) {
    errors.city = i18n.t('common:choose_city_from_list');
  }
  const errorsQuestions = reduceIndexed((acc, question, idx) => {
    const choiceQuestionsErrors = validateChoiceQuestionValues(
      question.question_data,
    );
    const codeQuestionsErrors = validateCodeQuestionValues(
      question.question_data,
    );
    const questonData = {
      question_data: {
        ...(!path('question_data.name', question) && {
          name: i18n.t('common:required_field'),
        }),
        ...(equals(question.type, 'choice') &&
          !isEmpty(choiceQuestionsErrors) && {
            answers: choiceQuestionsErrors,
          }),
        ...(equals(question.type, 'code') &&
          !isEmpty(codeQuestionsErrors) && { testcases: codeQuestionsErrors }),
      },
    };
    if (!isEmpty(questonData.question_data)) {
      acc[idx] = questonData;
    }

    return acc;
  }, [])(values.questions);
  if (is(Array, errorsQuestions) && errorsQuestions.length > 0) {
    errors.questions = errorsQuestions;
  }

  return errors;
};

export default validate;
