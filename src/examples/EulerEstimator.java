import java.io.IOException;
import java.util.StringTokenizer; 
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.conf.Configured;
import org.apache.hadoop.fs.Path;
// import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.TextInputFormat;
import org.apache.hadoop.mapreduce.lib.output.TextOutputFormat;
import org.apache.hadoop.mapreduce.lib.output.NullOutputFormat;
import org.apache.hadoop.mapreduce.lib.input.FileSplit;
import org.apache.hadoop.util.Tool;
import org.apache.hadoop.util.ToolRunner;
import java.util.Random;

public class EulerEstimator extends Configured implements Tool {

	public static class TokenizerMapper
	extends Mapper<LongWritable, Text, Text, LongPairWritable>{

		@Override
		public void map(LongWritable key, Text value, Context context
				) throws IOException, InterruptedException {

			// Parse input.
			long iterationsNumber = Integer.parseInt(value.toString());

			// Iterate iterationsNumber times.
			long fileNameHashCode = ((FileSplit) context.getInputSplit()).getPath().getName().hashCode();
			long seedValue = fileNameHashCode + key.get();
			Random rand = new Random(seedValue);
			int count = 0;
			for (int i = 1; i <= iterationsNumber; i++) {
				double sum = 0.0d;
				while (sum < 1) {
					sum += rand.nextDouble();
					count++;
				}
			}
			context.getCounter("Euler", "iterations").increment(iterationsNumber);
			context.getCounter("Euler", "count").increment(count);
		}

	}
 
	public static void main(String[] args) throws Exception {
		int res = ToolRunner.run(new Configuration(), new EulerEstimator(), args);
		System.exit(res);
	}
 
	@Override
	public int run(String[] args) throws Exception {
		Configuration conf = this.getConf();
		Job job = Job.getInstance(conf, "euler estimator");
		job.setJarByClass(EulerEstimator.class);
 
		job.setInputFormatClass(TextInputFormat.class);
 
		job.setMapperClass(TokenizerMapper.class);
		// job.setCombinerClass(SumCombiner.class);
		// job.setReducerClass(AverageReducer.class);

		job.setOutputKeyClass(NullOutputFormat.class);
		job.setOutputValueClass(NullOutputFormat.class);
		job.setOutputFormatClass(NullOutputFormat.class);
		TextInputFormat.addInputPath(job, new Path(args[0]));
		TextOutputFormat.setOutputPath(job, new Path(args[1]));
 
		return job.waitForCompletion(true) ? 0 : 1;
	}
}
